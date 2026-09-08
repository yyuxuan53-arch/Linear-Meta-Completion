#include "kilolib.h"
#include <stdint.h>
#include <stdlib.h>


/* ============================================================
 * BATTERY FLOODING: FIVE-UID POSITIVE CONTROL
 *
 * PHYSICAL SWARM:
 *
 *      100 Kilobots
 *
 * FLOODING TABLE:
 *
 *      capacity = 100 distinct UIDs
 *
 * This diagnostic firmware turns blue after collecting five distinct UIDs.
 * It validates reception, table merging, forwarding, counting, and the blue
 * LED trigger. It is not evidence of 100-robot meta-completion.
 *
 * BLUE iff five distinct UIDs are present in the local flooding table.
 *
 *
 * IMPORTANT:
 *
 * Battery completion is monotonic:
 *
 *      0 -> 1
 *
 * Therefore no version number is required.
 *
 * If a stored UID changes from:
 *
 *      state 0 -> received state 1
 *
 * memory is immediately updated to 1.
 *
 *
 * AFTER BLUE:
 *
 *      BLUE remains latched
 *      remain stationary
 *      continue receiving
 *      continue merging UID information
 *      continue collecting up to 100 UIDs
 *      continue transmitting
 *      continue cyclic flooding
 *
 * ============================================================ */


/* ============================================================
 * CONFIGURATION
 * ============================================================ */

#define SWARM_SIZE                  100

#define MEMORY_SIZE                 SWARM_SIZE

#define DETECTION_UID_LIMIT         5


#define TICKS_PER_SECOND            32

#define BATTERY_STEP                1

#define BROADCAST_INTERVAL_TICKS    8


/* ============================================================
 * STARTUP
 * ============================================================ */

#define STARTUP_FLASHES             5

#define FLASH_HALF_PERIOD_TICKS     8


/* ============================================================
 * FLOODING PACKET
 * ============================================================ */

#define MAX_RECORDS_PER_PACKET      4

#define FLOODING_MARKER_MASK        0x80

#define RECORD_COUNT_MASK           0x07


/* ============================================================
 * FLOODING TABLE ENTRY
 * ============================================================ */

typedef struct
{
    uint16_t agent_id;

    uint8_t agent_state;

} flooding_entry_t;


/* ============================================================
 * COMMUNICATION
 * ============================================================ */

message_t tx_message;


uint8_t tx_busy =
    0;


uint32_t last_broadcast_tick =
    0;


uint8_t tx_table_index =
    0;


uint8_t last_packet_record_count =
    0;


/* ============================================================
 * BATTERY
 * ============================================================ */

uint8_t battery =
    0;


/*
 * Local task state.
 *
 * 0 = incomplete
 * 1 = complete
 *
 * Monotonic:
 *
 *      0 -> 1
 */

uint8_t my_state =
    0;


uint32_t last_battery_tick =
    0;


/* ============================================================
 * IDENTITY
 * ============================================================ */

uint16_t my_id =
    0;


/* ============================================================
 * META-COMPLETION
 * ============================================================ */

/*
 * BLUE latch.
 *
 * once 1:
 *
 *      never returns to 0
 */

uint8_t meta_complete =
    0;


/* ============================================================
 * FLOODING TABLE
 * ============================================================ */

/*
 * Capacity = 100 UIDs.
 */

flooding_entry_t memory[
    MEMORY_SIZE
];


uint8_t memory_count =
    0;


/* ============================================================
 * STARTUP
 * ============================================================ */

uint8_t startup_finished =
    0;


uint8_t startup_phase =
    0;


uint32_t startup_last_tick =
    0;


/* ============================================================
 * FIND UID
 * ============================================================ */

uint8_t find_memory_index(
    uint16_t id
)
{
    uint8_t i;


    for (
        i = 0;
        i < memory_count;
        i++
    )
    {
        if (
            memory[i].agent_id
            ==
            id
        )
        {
            return i;
        }
    }


    return 255;
}


/* ============================================================
 * INSERT NEW UID
 * ============================================================ */

uint8_t insert_new_record(
    uint16_t id,
    uint8_t state
)
{
    uint8_t index;


    /* State must be binary */

    if (
        state
        >
        1
    )
    {
        return 0;
    }


    /* Maximum 100 distinct UIDs */

    if (
        memory_count
        >=
        MEMORY_SIZE
    )
    {
        return 0;
    }


    index =
        memory_count;


    memory[index].agent_id =
        id;


    memory[index].agent_state =
        state;


    memory_count++;


    return 1;
}


/* ============================================================
 * INITIALISE TABLE
 * ============================================================ */

void initialise_flooding_table(void)
{
    uint8_t i;


    for (
        i = 0;
        i < MEMORY_SIZE;
        i++
    )
    {
        memory[i].agent_id =
            0;


        memory[i].agent_state =
            0;
    }


    memory_count =
        0;


    tx_table_index =
        0;


    last_packet_record_count =
        0;


    /*
     * Every robot knows itself initially.
     */

    insert_new_record(

        my_id,

        my_state
    );
}


/* ============================================================
 * UPDATE OWN RECORD
 * ============================================================ */

void update_self_record(void)
{
    uint8_t idx;


    idx =
        find_memory_index(
            my_id
        );


    if (
        idx
        ==
        255
    )
    {
        insert_new_record(

            my_id,

            my_state
        );


        return;
    }


    /*
     * Own state is authoritative.
     */

    memory[idx].agent_state =
        my_state;
}


/* ============================================================
 * MERGE RECEIVED RECORD
 *
 * Battery state is monotonic:
 *
 *      0 -> 1
 *
 * Therefore:
 *
 *      unknown UID:
 *          store state
 *
 *      known UID state 0
 *      received state 1:
 *          update to 1
 *
 *      known UID state 1
 *      received state 0:
 *          ignore stale 0
 *
 * ============================================================ */

void merge_flooding_record(
    uint16_t id,
    uint8_t state
)
{
    uint8_t idx;


    if (
        state
        >
        1
    )
    {
        return;
    }


    /*
     * Never overwrite SELF
     * from network information.
     */

    if (
        id
        ==
        my_id
    )
    {
        return;
    }


    idx =
        find_memory_index(
            id
        );


    /* ========================================================
     * NEW UID
     * ======================================================== */

    if (
        idx
        ==
        255
    )
    {
        insert_new_record(

            id,

            state
        );


        return;
    }


    /* ========================================================
     * KNOWN UID:
     *
     * immediately update:
     *
     *      0 -> 1
     * ======================================================== */

    if (
        memory[idx].agent_state
        ==
        0

        &&

        state
        ==
        1
    )
    {
        memory[idx].agent_state =
            1;
    }
}


/* ============================================================
 * META-COMPLETION CHECK
 *
 * Positive-control trigger: five distinct UIDs have been collected.
 *
 * ============================================================ */

uint8_t check_meta_completion(void)
{
    return memory_count >= DETECTION_UID_LIMIT;
}


/* ============================================================
 * UPDATE META-COMPLETION
 * ============================================================ */

void update_meta_completion(void)
{
    /*
     * BLUE is latched.
     */

    if (
        meta_complete
    )
    {
        return;
    }


    if (
        check_meta_completion()
    )
    {
        meta_complete =
            1;
    }
}


/* ============================================================
 * LED
 * ============================================================ */

void update_led(void)
{
    if (
        !startup_finished
    )
    {
        return;
    }


    /* ========================================================
     * BLUE
     * ======================================================== */

    if (
        meta_complete
    )
    {
        set_color(
            RGB(0,0,3)
        );


        return;
    }


    /* ========================================================
     * GREEN
     * ======================================================== */

    if (
        my_state
        ==
        1
    )
    {
        set_color(
            RGB(0,3,0)
        );


        return;
    }


    /* ========================================================
     * RED
     * ======================================================== */

    set_color(
        RGB(3,0,0)
    );
}


/* ============================================================
 * STARTUP
 * ============================================================ */

void startup_sequence(void)
{
    if (
        startup_finished
    )
    {
        return;
    }


    set_motors(
        0,
        0
    );


    if (
        (
            kilo_ticks
            -
            startup_last_tick
        )
        <
        FLASH_HALF_PERIOD_TICKS
    )
    {
        return;
    }


    startup_last_tick =
        kilo_ticks;


    startup_phase++;


    /* ========================================================
     * RED / OFF
     * ======================================================== */

    if (
        startup_phase
        %
        2
        ==
        0
    )
    {
        set_color(
            RGB(3,0,0)
        );
    }


    else
    {
        set_color(
            RGB(0,0,0)
        );
    }


    /* ========================================================
     * FORMAL t = 0
     * ======================================================== */

    if (
        startup_phase
        >=
        STARTUP_FLASHES * 2
    )
    {
        startup_finished =
            1;


        last_battery_tick =
            kilo_ticks;


        last_broadcast_tick =
            kilo_ticks;


        update_self_record();


        update_meta_completion();


        update_led();
    }
}


/* ============================================================
 * BATTERY UPDATE
 * ============================================================ */

void update_battery(void)
{
    /* ========================================================
     * ALREADY COMPLETE
     * ======================================================== */

    if (
        battery
        >=
        100
    )
    {
        battery =
            100;


        my_state =
            1;


        /*
         * Keep own table entry synchronised.
         */

        update_self_record();


        return;
    }


    /* ========================================================
     * +1 EVERY SECOND
     * ======================================================== */

    if (
        (
            kilo_ticks
            -
            last_battery_tick
        )
        >=
        TICKS_PER_SECOND
    )
    {
        last_battery_tick +=
            TICKS_PER_SECOND;


        if (
            battery
            <=
            (
                100
                -
                BATTERY_STEP
            )
        )
        {
            battery +=
                BATTERY_STEP;
        }


        else
        {
            battery =
                100;
        }


        /* ====================================================
         * LOCAL COMPLETION
         * ==================================================== */

        if (
            battery
            >=
            100
        )
        {
            battery =
                100;


            my_state =
                1;


            /*
             * Immediately update SELF UID state:
             *
             *      0 -> 1
             */

            update_self_record();


            /*
             * The final missing state may now be complete.
             */

            update_meta_completion();


            update_led();
        }
    }
}


/* ============================================================
 * PACK ONE UID RECORD
 * ============================================================ */

void pack_record(
    uint8_t record_number,
    uint8_t memory_index,
    uint8_t *header
)
{
    uint8_t low_byte_position;

    uint8_t state_bit;


    low_byte_position =
        1
        +
        (
            2
            *
            record_number
        );


    /* UID low */

    tx_message.data[
        low_byte_position
    ] =
        (uint8_t)
        (
            memory[
                memory_index
            ].agent_id

            &

            0xFF
        );


    /* UID high */

    tx_message.data[
        low_byte_position + 1
    ] =
        (uint8_t)
        (
            (
                memory[
                    memory_index
                ].agent_id

                >>

                8
            )

            &

            0xFF
        );


    /* State bit */

    state_bit =
        3
        +
        record_number;


    if (
        memory[
            memory_index
        ].agent_state
        ==
        1
    )
    {
        *header |=
            (
                1
                <<
                state_bit
            );
    }
}


/* ============================================================
 * BUILD NEXT CYCLIC FLOODING PACKET
 * ============================================================ */

void prepare_flooding_message(void)
{
    uint8_t i;

    uint8_t header;

    uint8_t count;

    uint8_t memory_index;


    /* ========================================================
     * CLEAR PACKET
     * ======================================================== */

    for (
        i = 0;
        i < 9;
        i++
    )
    {
        tx_message.data[i] =
            0;
    }


    header =
        FLOODING_MARKER_MASK;


    count =
        0;


    if (
        memory_count
        >
        0
    )
    {
        /* ====================================================
         * WRAP TABLE CURSOR
         * ==================================================== */

        if (
            tx_table_index
            >=
            memory_count
        )
        {
            tx_table_index =
                0;
        }


        memory_index =
            tx_table_index;


        /* ====================================================
         * PACK UP TO FOUR UIDs
         * ==================================================== */

        while (
            memory_index
            <
            memory_count

            &&

            count
            <
            MAX_RECORDS_PER_PACKET
        )
        {
            pack_record(

                count,

                memory_index,

                &header
            );


            count++;


            memory_index++;
        }
    }


    /* ========================================================
     * RECORD COUNT
     * ======================================================== */

    header |=
        (
            count
            &
            RECORD_COUNT_MASK
        );


    tx_message.data[0] =
        header;


    last_packet_record_count =
        count;


    tx_message.type =
        NORMAL;


    tx_message.crc =
        message_crc(
            &tx_message
        );
}


/* ============================================================
 * TX CALLBACK
 *
 * BLUE continues transmitting.
 * ============================================================ */

message_t *message_tx(void)
{
    if (
        !startup_finished
    )
    {
        return 0;
    }


    if (
        tx_busy
    )
    {
        return
            &tx_message;
    }


    return 0;
}


/* ============================================================
 * TX SUCCESS
 * ============================================================ */

void message_tx_success(void)
{
    tx_busy =
        0;


    if (
        last_packet_record_count
        ==
        0
    )
    {
        return;
    }


    tx_table_index +=
        last_packet_record_count;


    if (
        tx_table_index
        >=
        memory_count
    )
    {
        tx_table_index =
            0;
    }
}


/* ============================================================
 * DECODE UID
 * ============================================================ */

uint16_t decode_packet_uid(
    message_t *msg,
    uint8_t record_number
)
{
    uint8_t low_byte_position;


    low_byte_position =
        1
        +
        (
            2
            *
            record_number
        );


    return

        (uint16_t)
        msg->data[
            low_byte_position
        ]

        |

        (
            (uint16_t)
            msg->data[
                low_byte_position + 1
            ]

            <<

            8
        );
}


/* ============================================================
 * DECODE STATE
 * ============================================================ */

uint8_t decode_packet_state(
    uint8_t header,
    uint8_t record_number
)
{
    uint8_t state_bit;


    state_bit =
        3
        +
        record_number;


    return

        (
            header

            >>

            state_bit
        )

        &

        0x01;
}


/* ============================================================
 * RECEIVE CALLBACK
 *
 * BLUE continues receiving.
 * ============================================================ */

void message_rx(
    message_t *msg,
    distance_measurement_t *distance
)
{
    uint8_t header;

    uint8_t record_count;

    uint8_t record_number;

    uint16_t received_id;

    uint8_t received_state;


    (void)distance;


    if (
        !startup_finished
    )
    {
        return;
    }


    /*
     * NO meta_complete return.
     *
     * BLUE robots continue RX.
     */


    if (
        message_crc(msg)
        !=
        msg->crc
    )
    {
        return;
    }


    if (
        msg->type
        !=
        NORMAL
    )
    {
        return;
    }


    header =
        msg->data[0];


    /* ========================================================
     * MARKER
     * ======================================================== */

    if (
        (
            header
            &
            FLOODING_MARKER_MASK
        )
        ==
        0
    )
    {
        return;
    }


    /* ========================================================
     * RECORD COUNT
     * ======================================================== */

    record_count =
        header
        &
        RECORD_COUNT_MASK;


    if (
        record_count
        >
        MAX_RECORDS_PER_PACKET
    )
    {
        return;
    }


    /* ========================================================
     * PROCESS ALL VALID RECORDS
     * ======================================================== */

    for (
        record_number = 0;
        record_number < record_count;
        record_number++
    )
    {
        received_id =
            decode_packet_uid(

                msg,

                record_number
            );


        received_state =
            decode_packet_state(

                header,

                record_number
            );


        /*
         * Existing UID state may immediately
         * update from:
         *
         *      0 -> 1
         */

        merge_flooding_record(

            received_id,

            received_state
        );
    }


    /* ========================================================
     * SELF AUTHORITATIVE
     * ======================================================== */

    update_self_record();


    /* ========================================================
     * CHECK FIVE-UID CONTROL TRIGGER
     * ======================================================== */

    update_meta_completion();


    update_led();
}


/* ============================================================
 * COMMUNICATION STEP
 * ============================================================ */

void communication_step(void)
{
    if (
        !startup_finished
    )
    {
        return;
    }


    /*
     * BLUE continues communication.
     */


    if (
        tx_busy
    )
    {
        return;
    }


    /* ========================================================
     * 8 TICKS
     * ======================================================== */

    if (
        (
            kilo_ticks
            -
            last_broadcast_tick
        )
        <
        BROADCAST_INTERVAL_TICKS
    )
    {
        return;
    }


    last_broadcast_tick =
        kilo_ticks;


    update_self_record();


    /*
     * Build packet from CURRENT memory states.
     */

    prepare_flooding_message();


    tx_busy =
        1;
}


/* ============================================================
 * SETUP
 * ============================================================ */

void setup(void)
{
    set_motors(
        0,
        0
    );


    my_id =
        (uint16_t)kilo_uid;


    /* ========================================================
     * INITIAL BATTERY = 0
     * ======================================================== */

    battery = 0;
    my_state = 0;


    meta_complete =
        0;


    /* ========================================================
     * TABLE
     *
     * Capacity 100.
     * Initially SELF only.
     * ======================================================== */

    initialise_flooding_table();


    /* ========================================================
     * COMMUNICATION
     * ======================================================== */

    tx_busy =
        0;


    tx_table_index =
        0;


    last_packet_record_count =
        0;


    prepare_flooding_message();


    last_broadcast_tick =
        kilo_ticks;


    /* ========================================================
     * BATTERY TIMER
     * ======================================================== */

    last_battery_tick =
        kilo_ticks;


    /* ========================================================
     * STARTUP
     * ======================================================== */

    startup_finished =
        0;


    startup_phase =
        0;


    startup_last_tick =
        kilo_ticks;


    set_color(
        RGB(3,0,0)
    );
}


/* ============================================================
 * MAIN LOOP
 * ============================================================ */

void loop(void)
{
    /* ========================================================
     * STARTUP
     * ======================================================== */

    if (
        !startup_finished
    )
    {
        set_motors(
            0,
            0
        );


        startup_sequence();


        return;
    }


    /* ========================================================
     * ALWAYS STATIONARY
     * ======================================================== */

    set_motors(
        0,
        0
    );


    /* ========================================================
     * BATTERY
     * ======================================================== */

    update_battery();


    /* ========================================================
     * SELF RECORD
     * ======================================================== */

    update_self_record();


    /* ========================================================
     * META-COMPLETION
     * ======================================================== */

    update_meta_completion();


    /* ========================================================
     * LED
     * ======================================================== */

    update_led();


    /* ========================================================
     * FLOODING CONTINUES AFTER BLUE
     * ======================================================== */

    communication_step();
}


/* ============================================================
 * MAIN
 * ============================================================ */

int main(void)
{
    kilo_init();


    kilo_message_tx =
        message_tx;


    kilo_message_tx_success =
        message_tx_success;


    kilo_message_rx =
        message_rx;


    kilo_start(
        setup,
        loop
    );


    return 0;
}
