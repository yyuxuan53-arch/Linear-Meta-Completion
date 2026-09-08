#include "kilolib.h"
#include <stdint.h>

/* Final task-only firmware (29 August): battery ground-truth baseline. */

#define BATTERY_MAX          100U
#define BATTERY_STEP         1U
#define TICKS_PER_SECOND     32UL
#define STARTUP_FLASHES      5U
#define STARTUP_HALF_PERIOD  8UL

uint8_t battery = 0;
uint8_t local_complete = 0;
uint8_t startup_finished = 0;
uint8_t startup_phase = 0;
uint32_t startup_last_tick = 0;
uint32_t last_battery_tick = 0;

static void startup_step(void)
{
    if ((kilo_ticks - startup_last_tick) < STARTUP_HALF_PERIOD) return;
    startup_last_tick = kilo_ticks;
    startup_phase++;
    set_color((startup_phase & 1U) ? RGB(0,0,0) : RGB(3,0,0));

    if (startup_phase >= STARTUP_FLASHES * 2U)
    {
        startup_finished = 1U;
        battery = 0;
        local_complete = 0;
        last_battery_tick = kilo_ticks;
        set_color(RGB(3,0,0));
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
            local_complete = 1U;
            break;
        }
        battery += BATTERY_STEP;
    }
}

void setup(void)
{
    set_motors(0, 0);
    set_color(RGB(3,0,0));
    startup_last_tick = kilo_ticks;
    last_battery_tick = kilo_ticks;
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
    set_color(local_complete ? RGB(0,3,0) : RGB(3,0,0));
}

int main(void)
{
    kilo_init();
    kilo_start(setup, loop);
    return 0;
}
