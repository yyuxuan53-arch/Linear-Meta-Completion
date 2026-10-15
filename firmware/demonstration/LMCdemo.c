/* All stages: red = local incomplete, green = local complete, blue = meta-complete. */
#include "kilolib.h"
#include <stdint.h>
#define PHASE_BATTERY 0U
#define PHASE_BATTERY_BLUE 1U
#define PHASE_VOTING 2U
#define PHASE_VOTING_BLUE 3U
#define PHASE_ACTION 4U
#define PHASE_FINAL_BLUE 5U
#define DECISION_LEFT 0U
#define DECISION_RIGHT 1U
#define PROTOCOL_MAGIC 0xB7U
#define BELIEF_SCALE 10000UL
#define META_THRESHOLD 9900U
#define K1 5000UL
#define K2 4300UL
#define TICKS_PER_SECOND 32UL
#define BROADCAST_TICKS 8UL
#define BLUE_HOLD_TICKS 32UL
#define STARTUP_FLASHES 5U
#define STARTUP_HALF_TICKS 8UL
#define BATTERY_MAX 100U
#define BATTERY_STEP 2U
#define VOTING_STABILITY_COUNT 10U
#define ACTION_LEFT_DURATION_SECONDS 10UL
#define ACTION_RIGHT_DURATION_SECONDS 5UL
#define ACTION_LEFT_DURATION_TICKS (ACTION_LEFT_DURATION_SECONDS * TICKS_PER_SECOND)
#define ACTION_RIGHT_DURATION_TICKS (ACTION_RIGHT_DURATION_SECONDS * TICKS_PER_SECOND)
message_t tx_message;
uint8_t phase = PHASE_BATTERY;
uint8_t decision = DECISION_LEFT;
uint8_t battery = 0U;
uint8_t battery_local_complete = 0U;
uint16_t battery_belief = 0U;
uint8_t voting_same_count = 0U;
uint8_t voting_local_complete = 0U;
uint16_t voting_belief = 0U;
uint8_t action_local_complete = 0U;
uint16_t action_belief = 0U;
uint32_t action_start_tick = 0UL;
volatile uint8_t rx_phase = PHASE_BATTERY;
volatile uint8_t rx_decision = DECISION_LEFT;
volatile uint16_t rx_battery_belief = 0U;
volatile uint16_t rx_voting_belief = 0U;
volatile uint16_t rx_action_belief = 0U;
volatile uint8_t rx_pending = 0U;
volatile uint8_t tx_busy = 0U;
uint32_t last_broadcast_tick = 0UL;
uint8_t startup_finished = 0U;
uint8_t startup_phase = 0U;
uint32_t startup_last_tick = 0UL;
uint32_t last_battery_tick = 0UL;
uint32_t blue_started_tick = 0UL;
static void stop(void) { set_motors(0, 0); }
#define TURN_PWM_INCREMENT 30U
/* Use a wider intermediate so adding 30 cannot wrap around. */
static uint8_t increased_pwm(uint8_t calibrated)
{
    uint16_t value = (uint16_t)calibrated + TURN_PWM_INCREMENT;
    return (uint8_t)(value > 255U ? 255U : value);
}
/* LEFT decision: left motor off, right motor calibrated PWM + 30. */
static void turn_left(void) { set_motors(0, increased_pwm(kilo_turn_right)); }
/* RIGHT decision: right motor off, left motor calibrated PWM + 30. */
static void turn_right(void) { set_motors(increased_pwm(kilo_turn_left), 0); }
static void encode_uint16(uint16_t value, uint8_t *data)
{
    data[0] = (uint8_t)(value & 0xFFU);
    data[1] = (uint8_t)((value >> 8) & 0xFFU);
}
static uint16_t decode_uint16(const uint8_t *data)
{
    uint16_t value;
    value = (uint16_t)data[0];
    value |= ((uint16_t)data[1] << 8);
    if (value > BELIEF_SCALE)
    {
        value = (uint16_t)BELIEF_SCALE;
    }
    return value;
}
static uint16_t lmc_update(uint16_t own, uint16_t neighbour, uint8_t local_complete)
{
    uint32_t numerator;
    uint32_t new_belief;
    if (!local_complete)
    {
        return 0U;
    }
    numerator = K1 * (uint32_t)own + K2 * (uint32_t)neighbour +
                (BELIEF_SCALE - K1 - K2) * BELIEF_SCALE;
    new_belief = numerator / BELIEF_SCALE;
    if (new_belief > BELIEF_SCALE)
    {
        new_belief = BELIEF_SCALE;
    }
    return (uint16_t)new_belief;
}
static void prepare_message(void)
{
    uint8_t flags;
    tx_message.data[0] = PROTOCOL_MAGIC;
    tx_message.data[1] = (uint8_t)((phase & 0x07U) | ((decision & 0x01U) << 3));
    encode_uint16(battery_belief, &tx_message.data[2]);
    encode_uint16(voting_belief, &tx_message.data[4]);
    encode_uint16(action_belief, &tx_message.data[6]);
    flags = 0U;
    if (battery_local_complete)
    {
        flags |= 0x01U;
    }
    if (voting_local_complete)
    {
        flags |= 0x02U;
    }
    if (action_local_complete)
    {
        flags |= 0x04U;
    }
    tx_message.data[8] = flags;
    tx_message.type = NORMAL;
    tx_message.crc = message_crc(&tx_message);
}
message_t *message_tx(void)
{
    if (startup_finished && tx_busy)
    {
        return &tx_message;
    }
    return 0;
}
void message_tx_success(void) { tx_busy = 0U; }
void message_rx(message_t *message, distance_measurement_t *distance)
{
    uint8_t packed;
    uint8_t received_phase;
    uint8_t received_decision;
    (void)distance;
    if (!startup_finished)
    {
        return;
    }
    if (message->type != NORMAL)
    {
        return;
    }
    if (message_crc(message) != message->crc)
    {
        return;
    }
    if (message->data[0] != PROTOCOL_MAGIC)
    {
        return;
    }
    packed = message->data[1];
    received_phase = packed & 0x07U;
    received_decision = (packed >> 3) & 0x01U;
    if (received_phase > PHASE_FINAL_BLUE)
    {
        return;
    }
    rx_phase = received_phase;
    rx_decision = received_decision;
    rx_battery_belief = decode_uint16(&message->data[2]);
    rx_voting_belief = decode_uint16(&message->data[4]);
    rx_action_belief = decode_uint16(&message->data[6]);
    rx_pending = 1U;
}
static void startup_step(void)
{
    if ((kilo_ticks - startup_last_tick) < STARTUP_HALF_TICKS)
    {
        return;
    }
    startup_last_tick = kilo_ticks;
    startup_phase++;
    if (startup_phase & 1U)
    {
        set_color(RGB(0, 0, 0));
    }
    else
    {
        set_color(RGB(3, 0, 0));
    }
    if (startup_phase >= (STARTUP_FLASHES * 2U))
    {
        startup_finished = 1U;
        battery = (uint8_t)(rand_soft() % 101U);
        if (battery >= BATTERY_MAX)
        {
            battery = BATTERY_MAX;
            battery_local_complete = 1U;
        }
        else
        {
            battery_local_complete = 0U;
        }
        battery_belief = 0U;
        voting_belief = 0U;
        action_belief = 0U;
        last_battery_tick = kilo_ticks;
        last_broadcast_tick = kilo_ticks;
        if (battery_local_complete)
        {
            set_color(RGB(0, 3, 0));
        }
        else
        {
            set_color(RGB(3, 0, 0));
        }
    }
}
static void battery_step(void)
{
    while (!battery_local_complete &&
           (kilo_ticks - last_battery_tick) >= TICKS_PER_SECOND)
    {
        last_battery_tick += TICKS_PER_SECOND;
        if (battery >= (BATTERY_MAX - BATTERY_STEP))
        {
            battery = BATTERY_MAX;
            battery_local_complete = 1U;
        }
        else
        {
            battery += BATTERY_STEP;
        }
    }
    if (battery_local_complete)
    {
        set_color(RGB(0, 3, 0));
    }
    else
    {
        set_color(RGB(3, 0, 0));
    }
}
static void begin_voting(void)
{
    phase = PHASE_VOTING;
    decision = (uint8_t)(rand_soft() & 1U);
    voting_same_count = 0U;
    voting_local_complete = 0U;
    voting_belief = 0U;
    set_color(RGB(3, 0, 0));
}
static void begin_action(void)
{
    phase = PHASE_ACTION;
    action_local_complete = 0U;
    action_belief = 0U;
    set_color(RGB(3, 0, 0));
    /* Apply the startup pulse once, only to the selected motor. */
    if (decision == DECISION_LEFT)
    {
        set_motors(0, 255);
        delay(15);
        turn_left();
    }
    else
    {
        set_motors(255, 0);
        delay(15);
        turn_right();
    }
    action_start_tick = kilo_ticks;
}
static void action_step(void)
{
    uint32_t duration_ticks = (decision == DECISION_LEFT) ? ACTION_LEFT_DURATION_TICKS
                                                          : ACTION_RIGHT_DURATION_TICKS;
    if (action_local_complete)
    {
        stop();
        set_color(RGB(0, 3, 0));
        return;
    }
    if ((uint32_t)(kilo_ticks - action_start_tick) >= duration_ticks)
    {
        stop();
        action_local_complete = 1U;
        set_color(RGB(0, 3, 0));
        return;
    }
    set_color(RGB(3, 0, 0));
    if (decision == DECISION_LEFT)
        turn_left();
    else
        turn_right();
}
static void process_message(void)
{
    uint8_t neighbour_phase;
    uint8_t neighbour_decision;
    uint16_t neighbour_battery_belief;
    uint16_t neighbour_voting_belief;
    uint16_t neighbour_action_belief;
    if (!rx_pending)
    {
        return;
    }
    neighbour_phase = rx_phase;
    neighbour_decision = rx_decision;
    neighbour_battery_belief = rx_battery_belief;
    neighbour_voting_belief = rx_voting_belief;
    neighbour_action_belief = rx_action_belief;
    rx_pending = 0U;
    if (phase == PHASE_BATTERY)
    {
        battery_belief =
            lmc_update(battery_belief, neighbour_battery_belief, battery_local_complete);
        if (battery_belief >= META_THRESHOLD)
        {
            phase = PHASE_BATTERY_BLUE;
            blue_started_tick = kilo_ticks;
            stop();
            set_color(RGB(0, 0, 3));
        }
        return;
    }
    if (phase == PHASE_VOTING)
    {
        if (neighbour_phase >= PHASE_VOTING)
        {
            if (neighbour_decision != decision)
            {
                decision = neighbour_decision;
                voting_same_count = 0U;
                voting_local_complete = 0U;
                voting_belief = 0U;
            }
            else
            {
                if (voting_same_count < VOTING_STABILITY_COUNT)
                {
                    voting_same_count++;
                }
                if (voting_same_count >= VOTING_STABILITY_COUNT)
                {
                    voting_local_complete = 1U;
                }
                else
                {
                    voting_local_complete = 0U;
                }
            }
            voting_belief =
                lmc_update(voting_belief, neighbour_voting_belief, voting_local_complete);
            if (voting_belief >= META_THRESHOLD)
            {
                phase = PHASE_VOTING_BLUE;
                blue_started_tick = kilo_ticks;
                stop();
                set_color(RGB(0, 0, 3));
            }
        }
        return;
    }
    if (phase == PHASE_ACTION)
    {
        if (neighbour_phase >= PHASE_ACTION)
        {
            action_belief =
                lmc_update(action_belief, neighbour_action_belief, action_local_complete);
            if (action_belief >= META_THRESHOLD)
            {
                phase = PHASE_FINAL_BLUE;
                stop();
                set_color(RGB(0, 0, 3));
            }
        }
        return;
    }
}
static void communication_step(void)
{
    if (tx_busy)
    {
        return;
    }
    if ((kilo_ticks - last_broadcast_tick) < BROADCAST_TICKS)
    {
        return;
    }
    last_broadcast_tick = kilo_ticks;
    prepare_message();
    tx_busy = 1U;
}
void setup(void)
{
    uint8_t seed;
    stop();
    seed = rand_hard();
    rand_seed((uint8_t)(seed ^ (uint8_t)kilo_uid));
    phase = PHASE_BATTERY;
    decision = DECISION_LEFT;
    battery = 0U;
    battery_local_complete = 0U;
    battery_belief = 0U;
    voting_same_count = 0U;
    voting_local_complete = 0U;
    voting_belief = 0U;
    action_local_complete = 0U;
    action_belief = 0U;
    tx_busy = 0U;
    last_broadcast_tick = kilo_ticks;
    startup_finished = 0U;
    startup_phase = 0U;
    startup_last_tick = kilo_ticks;
    set_color(RGB(3, 0, 0));
    prepare_message();
}
void loop(void)
{
    if (!startup_finished)
    {
        stop();
        startup_step();
        return;
    }
    process_message();
    if (phase == PHASE_BATTERY)
    {
        stop();
        battery_step();
    }
    else if (phase == PHASE_BATTERY_BLUE)
    {
        stop();
        set_color(RGB(0, 0, 3));
        if ((kilo_ticks - blue_started_tick) >= BLUE_HOLD_TICKS)
        {
            begin_voting();
        }
    }
    else if (phase == PHASE_VOTING)
    {
        stop();
        if (voting_local_complete)
            set_color(RGB(0, 3, 0));
        else
            set_color(RGB(3, 0, 0));
    }
    else if (phase == PHASE_VOTING_BLUE)
    {
        stop();
        set_color(RGB(0, 0, 3));
        if ((kilo_ticks - blue_started_tick) >= BLUE_HOLD_TICKS)
        {
            begin_action();
        }
    }
    else if (phase == PHASE_ACTION)
    {
        action_step();
    }
    else if (phase == PHASE_FINAL_BLUE)
    {
        stop();
        set_color(RGB(0, 0, 3));
    }
    communication_step();
}
int main(void)
{
    kilo_init();
    kilo_message_rx = message_rx;
    kilo_message_tx = message_tx;
    kilo_message_tx_success = message_tx_success;
    kilo_start(setup, loop);
    return 0;
}

