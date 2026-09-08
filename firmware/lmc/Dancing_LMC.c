#include "kilolib.h"
#include <stdint.h>

/* Final physical firmware (29 August): random-walk task + LMC. */

#define TICKS_PER_SECOND          32UL
#define BROADCAST_INTERVAL_TICKS  8UL
#define STARTUP_FLASHES           5U
#define STARTUP_HALF_PERIOD       8UL

#define MIN_WALK_SECONDS          5U
#define MAX_WALK_SECONDS          15U
#define RANDOM_TURN_TICKS         16UL
#define FORWARD_SPEED_BOOST       30U
#define TURN_LEFT                 0U

#define BELIEF_SCALE              10000UL
#define K1                        5000UL  /* 0.50 */
#define K2                        4800UL  /* 0.48 */
#define META_THRESHOLD            9900U   /* 0.99 */
#define META_STABILITY_UPDATES    10U

message_t tx_message;
volatile uint16_t received_belief = 0;
volatile uint8_t received_new_belief = 0;
volatile uint8_t tx_busy = 0;

uint16_t meta_belief = 0;
uint8_t local_complete = 0;
uint8_t meta_complete = 0;
uint8_t threshold_count = 0;

uint8_t startup_finished = 0;
uint8_t startup_phase = 0;
uint32_t startup_last_tick = 0;
uint32_t last_broadcast_tick = 0;

uint32_t walk_start_tick = 0;
uint32_t walk_duration_ticks = 0;
uint32_t turn_trigger_ticks = 0;
uint32_t turn_start_tick = 0;
uint8_t turn_direction = TURN_LEFT;
uint8_t turn_started = 0;
uint8_t turn_finished = 0;

static uint8_t boosted_motor(uint8_t base)
{
    uint16_t value = (uint16_t)base + FORWARD_SPEED_BOOST;
    return (value > 255U) ? 255U : (uint8_t)value;
}

static uint16_t random_u16(void)
{
    return ((uint16_t)rand_soft() << 8) | (uint16_t)rand_soft();
}

static void move_forward_fast(void)
{
    spinup_motors();
    set_motors(boosted_motor(kilo_straight_left),
               boosted_motor(kilo_straight_right));
}

static void perform_turn(void)
{
    spinup_motors();
    if (turn_direction == TURN_LEFT)
    {
        set_motors(kilo_turn_left, 0);
    }
    else
    {
        set_motors(0, kilo_turn_right);
    }
}

static void prepare_message(void)
{
    uint8_t i;
    for (i = 0; i < 9; i++) tx_message.data[i] = 0;
    tx_message.data[0] = (uint8_t)(meta_belief & 0xFFU);
    tx_message.data[1] = (uint8_t)((meta_belief >> 8) & 0xFFU);
    tx_message.type = NORMAL;
    tx_message.crc = message_crc(&tx_message);
}

message_t *message_tx(void)
{
    return (startup_finished && tx_busy) ? &tx_message : 0;
}

void message_tx_success(void)
{
    tx_busy = 0;
}

void message_rx(message_t *message, distance_measurement_t *distance)
{
    uint16_t value;
    (void)distance;
    if (!startup_finished || message_crc(message) != message->crc ||
        message->type != NORMAL)
    {
        return;
    }

    value = (uint16_t)message->data[0] |
            ((uint16_t)message->data[1] << 8);
    if (value > BELIEF_SCALE) value = BELIEF_SCALE;
    received_belief = value;
    received_new_belief = 1;
}

static void initialise_random_walk(void)
{
    uint8_t seconds;
    uint32_t available;

    seconds = MIN_WALK_SECONDS +
              (uint8_t)(rand_soft() %
              (MAX_WALK_SECONDS - MIN_WALK_SECONDS + 1U));
    walk_duration_ticks = (uint32_t)seconds * TICKS_PER_SECOND;
    available = walk_duration_ticks - RANDOM_TURN_TICKS;
    turn_trigger_ticks = (uint32_t)(random_u16() % available);
    turn_direction = (uint8_t)(rand_soft() & 1U);
    turn_started = 0;
    turn_finished = 0;
    walk_start_tick = kilo_ticks;
}

static void startup_step(void)
{
    if ((kilo_ticks - startup_last_tick) < STARTUP_HALF_PERIOD) return;

    startup_last_tick = kilo_ticks;
    startup_phase++;
    set_color((startup_phase & 1U) ? RGB(0,0,0) : RGB(3,0,0));

    if (startup_phase >= STARTUP_FLASHES * 2U)
    {
        startup_finished = 1;
        local_complete = 0;
        meta_belief = 0;
        threshold_count = 0;
        last_broadcast_tick = kilo_ticks;
        initialise_random_walk();
        set_color(RGB(3,3,0));
    }
}

static void random_walk_step(void)
{
    uint32_t elapsed;

    if (local_complete)
    {
        set_motors(0, 0);
        return;
    }

    elapsed = kilo_ticks - walk_start_tick;
    if (elapsed >= walk_duration_ticks)
    {
        local_complete = 1;
        set_motors(0, 0);
        set_color(RGB(0,3,0));
        return;
    }

    set_color(RGB(3,3,0));
    if (!turn_started && elapsed >= turn_trigger_ticks)
    {
        turn_started = 1;
        turn_start_tick = kilo_ticks;
    }

    if (turn_started && !turn_finished)
    {
        if ((kilo_ticks - turn_start_tick) < RANDOM_TURN_TICKS)
        {
            perform_turn();
            return;
        }
        turn_finished = 1;
    }
    move_forward_fast();
}

static void process_received_belief(void)
{
    uint16_t neighbour;
    uint32_t numerator;

    if (!received_new_belief || meta_complete) return;
    neighbour = received_belief;
    received_new_belief = 0;

    if (!local_complete)
    {
        meta_belief = 0;
        threshold_count = 0;
        return;
    }

    numerator = K1 * (uint32_t)meta_belief +
                K2 * (uint32_t)neighbour +
                (BELIEF_SCALE - K1 - K2) * BELIEF_SCALE;
    meta_belief = (uint16_t)(numerator / BELIEF_SCALE);
    if (meta_belief > BELIEF_SCALE) meta_belief = BELIEF_SCALE;

    if (meta_belief >= META_THRESHOLD)
    {
        if (threshold_count < META_STABILITY_UPDATES) threshold_count++;
        if (threshold_count >= META_STABILITY_UPDATES) meta_complete = 1;
    }
    else
    {
        threshold_count = 0;
    }
}

static void communication_step(void)
{
    if (!startup_finished || tx_busy ||
        (kilo_ticks - last_broadcast_tick) < BROADCAST_INTERVAL_TICKS)
    {
        return;
    }
    last_broadcast_tick = kilo_ticks;
    prepare_message();
    tx_busy = 1;
}

void setup(void)
{
    uint8_t seed = rand_hard();
    rand_seed((uint8_t)(seed ^ (uint8_t)kilo_uid));
    set_motors(0, 0);
    set_color(RGB(3,0,0));
    startup_last_tick = kilo_ticks;
    last_broadcast_tick = kilo_ticks;
    prepare_message();
}

void loop(void)
{
    if (!startup_finished)
    {
        set_motors(0, 0);
        startup_step();
        return;
    }

    random_walk_step();
    process_received_belief();
    if (meta_complete)
    {
        set_motors(0, 0);
        set_color(RGB(0,0,3));
    }
    else if (local_complete)
    {
        set_color(RGB(0,3,0));
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
