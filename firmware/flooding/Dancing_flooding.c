#include "kilolib.h"
#include <stdint.h>

/* Final physical firmware (29 August): random-walk task + full flooding. */

#define SWARM_SIZE                 100U
#define MEMORY_SIZE                SWARM_SIZE
#define DETECTION_UID_LIMIT        SWARM_SIZE
#define BROADCAST_INTERVAL_TICKS   8UL
#define STARTUP_FLASHES            5U
#define STARTUP_HALF_PERIOD        8UL

#define TICKS_PER_SECOND           32UL
#define MIN_WALK_SECONDS           5U
#define MAX_WALK_SECONDS           15U
#define RANDOM_TURN_TICKS          16UL
#define FORWARD_SPEED_BOOST        30U
#define TURN_LEFT                  0U

#define FLOODING_MARKER_MASK       0x80U
#define RECORD_COUNT_MASK          0x07U
#define MAX_RECORDS_PER_PACKET     4U

typedef struct
{
    uint16_t uid;
    uint8_t state;
} flooding_entry_t;

message_t tx_message;
volatile uint8_t tx_busy = 0;
flooding_entry_t memory[MEMORY_SIZE];
uint8_t memory_count = 0;
uint8_t tx_table_index = 0;
uint8_t last_packet_record_count = 0;

uint8_t local_complete = 0;
uint8_t meta_complete = 0;
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

static uint8_t find_uid(uint16_t uid)
{
    uint8_t i;
    for (i = 0; i < memory_count; i++)
    {
        if (memory[i].uid == uid) return i;
    }
    return 255U;
}

static void merge_record(uint16_t uid, uint8_t state)
{
    uint8_t index = find_uid(uid);
    state = state ? 1U : 0U;
    if (index != 255U)
    {
        if (state) memory[index].state = 1U;
        return;
    }
    if (memory_count < MEMORY_SIZE)
    {
        memory[memory_count].uid = uid;
        memory[memory_count].state = state;
        memory_count++;
    }
}

static void update_own_record(void)
{
    merge_record((uint16_t)kilo_uid, local_complete);
}

static void check_meta_completion(void)
{
    uint8_t i;
    if (meta_complete || !local_complete ||
        memory_count < DETECTION_UID_LIMIT)
    {
        return;
    }
    for (i = 0; i < DETECTION_UID_LIMIT; i++)
    {
        if (!memory[i].state) return;
    }
    meta_complete = 1U;
}

static void prepare_flooding_message(void)
{
    uint8_t i;
    uint8_t count = 0;
    uint8_t header = FLOODING_MARKER_MASK;

    for (i = 0; i < 9; i++) tx_message.data[i] = 0;
    if (tx_table_index >= memory_count) tx_table_index = 0;

    while (count < MAX_RECORDS_PER_PACKET &&
           (uint8_t)(tx_table_index + count) < memory_count)
    {
        uint8_t index = (uint8_t)(tx_table_index + count);
        tx_message.data[1U + 2U * count] =
            (uint8_t)(memory[index].uid & 0xFFU);
        tx_message.data[2U + 2U * count] =
            (uint8_t)((memory[index].uid >> 8) & 0xFFU);
        if (memory[index].state) header |= (uint8_t)(1U << (3U + count));
        count++;
    }

    tx_message.data[0] = (uint8_t)(header | (count & RECORD_COUNT_MASK));
    last_packet_record_count = count;
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
    tx_table_index = (uint8_t)(tx_table_index + last_packet_record_count);
    if (tx_table_index >= memory_count) tx_table_index = 0;
}

void message_rx(message_t *message, distance_measurement_t *distance)
{
    uint8_t i;
    uint8_t count;
    uint8_t header;
    (void)distance;

    if (!startup_finished || message_crc(message) != message->crc ||
        message->type != NORMAL)
    {
        return;
    }
    header = message->data[0];
    if ((header & FLOODING_MARKER_MASK) == 0U) return;
    count = (uint8_t)(header & RECORD_COUNT_MASK);
    if (count > MAX_RECORDS_PER_PACKET) return;

    for (i = 0; i < count; i++)
    {
        uint16_t uid =
            (uint16_t)message->data[1U + 2U * i] |
            ((uint16_t)message->data[2U + 2U * i] << 8);
        uint8_t state = (uint8_t)((header >> (3U + i)) & 1U);
        merge_record(uid, state);
    }
    check_meta_completion();
}

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
        update_own_record();
        check_meta_completion();
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
        memory_count = 0;
        merge_record((uint16_t)kilo_uid, 0);
        last_broadcast_tick = kilo_ticks;
        initialise_random_walk();
        set_color(RGB(3,3,0));
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
    update_own_record();
    prepare_flooding_message();
    tx_busy = 1U;
}

void setup(void)
{
    uint8_t seed = rand_hard();
    rand_seed((uint8_t)(seed ^ (uint8_t)kilo_uid));
    set_motors(0, 0);
    set_color(RGB(3,0,0));
    startup_last_tick = kilo_ticks;
    last_broadcast_tick = kilo_ticks;
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
    check_meta_completion();
    if (meta_complete)
    {
        set_motors(0, 0);
        set_color(RGB(0,0,3));
    }
    else if (local_complete)
    {
        set_color(RGB(0,3,0));
    }
    else
    {
        set_color(RGB(3,3,0));
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
