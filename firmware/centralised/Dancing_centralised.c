#include "kilolib.h"
#include <stdint.h>

/* Final task-only firmware (29 August): random-walk ground-truth baseline. */

#define TICKS_PER_SECOND      32UL
#define STARTUP_FLASHES       5U
#define STARTUP_HALF_PERIOD   8UL
#define MIN_WALK_SECONDS      5U
#define MAX_WALK_SECONDS      15U
#define RANDOM_TURN_TICKS     16UL
#define FORWARD_SPEED_BOOST   30U
#define TURN_LEFT             0U

uint8_t local_complete = 0;
uint8_t startup_finished = 0;
uint8_t startup_phase = 0;
uint32_t startup_last_tick = 0;
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
    if (turn_direction == TURN_LEFT) set_motors(kilo_turn_left, 0);
    else set_motors(0, kilo_turn_right);
}

static void initialise_random_walk(void)
{
    uint8_t seconds = MIN_WALK_SECONDS +
        (uint8_t)(rand_soft() % (MAX_WALK_SECONDS - MIN_WALK_SECONDS + 1U));
    uint32_t available;

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
        startup_finished = 1U;
        local_complete = 0;
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
        local_complete = 1U;
        set_motors(0, 0);
        return;
    }

    if (!turn_started && elapsed >= turn_trigger_ticks)
    {
        turn_started = 1U;
        turn_start_tick = kilo_ticks;
    }
    if (turn_started && !turn_finished)
    {
        if ((kilo_ticks - turn_start_tick) < RANDOM_TURN_TICKS)
        {
            perform_turn();
            return;
        }
        turn_finished = 1U;
    }
    move_forward_fast();
}

void setup(void)
{
    uint8_t seed = rand_hard();
    rand_seed((uint8_t)(seed ^ (uint8_t)kilo_uid));
    set_motors(0, 0);
    set_color(RGB(3,0,0));
    startup_last_tick = kilo_ticks;
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
    set_color(local_complete ? RGB(0,3,0) : RGB(3,3,0));
}

int main(void)
{
    kilo_init();
    kilo_start(setup, loop);
    return 0;
}
