#include "kilolib.h"
#include <stdint.h>

/* Final physical firmware (29 August): battery task + LMC. */

#define BATTERY_MAX                100U
#define BATTERY_STEP               1U
#define TICKS_PER_SECOND           32UL
#define BROADCAST_INTERVAL_TICKS   8UL
#define STARTUP_FLASHES            5U
#define STARTUP_HALF_PERIOD        8UL
#define BELIEF_SCALE               10000U

static const float k1 = 0.50f;
static const float k2 = 0.43f;

message_t tx_message;
volatile uint16_t received_encoded_belief = 0;
volatile uint8_t received_new_belief = 0;
volatile uint8_t tx_busy = 0;

uint8_t battery = 0;
uint8_t local_complete = 0;
uint8_t meta_complete = 0;
float meta_belief = 0.0f;

uint8_t startup_finished = 0;
uint8_t startup_phase = 0;
uint32_t startup_last_tick = 0;
uint32_t last_battery_tick = 0;
uint32_t last_broadcast_tick = 0;

static void prepare_message(void)
{
    uint8_t i;
    uint16_t encoded;

    if (meta_belief < 0.0f) meta_belief = 0.0f;
    if (meta_belief > 1.0f) meta_belief = 1.0f;
    encoded = (uint16_t)(meta_belief * (float)BELIEF_SCALE);

    for (i = 0; i < 9; i++) tx_message.data[i] = 0;
    tx_message.data[0] = (uint8_t)(encoded & 0xFFU);
    tx_message.data[1] = (uint8_t)((encoded >> 8) & 0xFFU);
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
    uint16_t encoded;
    (void)distance;

    if (!startup_finished || message_crc(message) != message->crc ||
        message->type != NORMAL || meta_complete)
    {
        return;
    }

    encoded = (uint16_t)message->data[0] |
              ((uint16_t)message->data[1] << 8);
    if (encoded > BELIEF_SCALE) encoded = BELIEF_SCALE;
    received_encoded_belief = encoded;
    received_new_belief = 1;
}

static void update_colour(void)
{
    if (!startup_finished) return;
    if (meta_complete) set_color(RGB(0,0,3));
    else if (local_complete) set_color(RGB(0,3,0));
    else set_color(RGB(3,0,0));
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
        battery = 0;
        local_complete = 0;
        meta_belief = 0.0f;
        last_battery_tick = kilo_ticks;
        last_broadcast_tick = kilo_ticks;
        update_colour();
    }
}

static void update_battery(void)
{
    if (local_complete) return;

    while ((kilo_ticks - last_battery_tick) >= TICKS_PER_SECOND)
    {
        last_battery_tick += TICKS_PER_SECOND;
        if (battery >= BATTERY_MAX - BATTERY_STEP)
        {
            battery = BATTERY_MAX;
            local_complete = 1;
            break;
        }
        battery += BATTERY_STEP;
    }
}

static void process_received_belief(void)
{
    float neighbour;

    if (!received_new_belief || meta_complete) return;
    neighbour = (float)received_encoded_belief / (float)BELIEF_SCALE;
    received_new_belief = 0;

    if (!local_complete)
    {
        meta_belief = 0.0f;
        return;
    }

    meta_belief = k1 * meta_belief +
                  k2 * neighbour +
                  (1.0f - k1 - k2);
    if (meta_belief > 1.0f) meta_belief = 1.0f;
    if (meta_belief >= 0.99f) meta_complete = 1;
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
    set_motors(0, 0);
    battery = 0;
    local_complete = 0;
    meta_complete = 0;
    meta_belief = 0.0f;
    startup_last_tick = kilo_ticks;
    last_battery_tick = kilo_ticks;
    last_broadcast_tick = kilo_ticks;
    set_color(RGB(3,0,0));
    prepare_message();
}

void loop(void)
{
    set_motors(0, 0);
    if (!startup_finished)
    {
        startup_step();
        return;
    }

    update_battery();
    process_received_belief();
    update_colour();
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
