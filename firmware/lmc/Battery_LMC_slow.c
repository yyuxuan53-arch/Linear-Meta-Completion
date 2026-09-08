#include "kilolib.h"
#include <stdint.h>

/* Permanently unfinished battery robot used in partial-completion trials. */

#define BROADCAST_INTERVAL_TICKS  8UL
#define STARTUP_FLASHES           5U
#define STARTUP_HALF_PERIOD       8UL

message_t tx_message;
volatile uint8_t tx_busy = 0;
uint8_t startup_finished = 0;
uint8_t startup_phase = 0;
uint32_t startup_last_tick = 0;
uint32_t last_broadcast_tick = 0;

static void prepare_message(void)
{
    uint8_t i;
    for (i = 0; i < 9; i++) tx_message.data[i] = 0;
    /* P=0 is encoded in data[0:1]. */
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

static void startup_step(void)
{
    if ((kilo_ticks - startup_last_tick) < STARTUP_HALF_PERIOD) return;
    startup_last_tick = kilo_ticks;
    startup_phase++;
    set_color((startup_phase & 1U) ? RGB(0,0,0) : RGB(3,0,0));
    if (startup_phase >= STARTUP_FLASHES * 2U)
    {
        startup_finished = 1;
        last_broadcast_tick = kilo_ticks;
        set_color(RGB(3,0,0));
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
    set_motors(0, 0);
    set_color(RGB(3,0,0));
    startup_last_tick = kilo_ticks;
    last_broadcast_tick = kilo_ticks;
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
    set_color(RGB(3,0,0));
    communication_step();
}

int main(void)
{
    kilo_init();
    kilo_message_tx = message_tx;
    kilo_message_tx_success = message_tx_success;
    kilo_start(setup, loop);
    return 0;
}
