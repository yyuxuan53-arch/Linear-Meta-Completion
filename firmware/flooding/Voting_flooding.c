#include "kilolib.h"
#include <stdlib.h>
#include <stdint.h>


/* =========================================================
   VOTING TASK + FULL-TABLE FLOODING

   PHYSICAL SWARM:
       100 robots

   MEMORY:
       store up to 100 distinct UIDs

   DETECTION:
       all 100 distinct UIDs must be collected and complete

   BLUE WHEN:

       own s == 1

       AND

       memory_count >= 100

       AND

       all 100 stored UID states are 1


   IMPORTANT:

       Voting completion state s is REVERSIBLE.

       same opinion for 10 received messages:
           s = 1

       different opinion:
           adopt received opinion
           same_count = 0
           s = 0


       EVERY TIME own s changes:

           own_version++
           own UID record in memory is updated immediately


       FLOODED RECORD:

           UID
           state
           version


       When another robot receives a newer version:

           its stored state for that UID is replaced.


   AFTER BLUE:

       BLUE remains latched

       BUT robot still:

           receives
           votes
           changes s
           updates own UID record
           merges received UID records
           transmits
           floods complete table

       Therefore BLUE does NOT freeze the protocol.


   MOVEMENT:

       NONE


   COMMUNICATION:

       one packet every 8 ticks

       each packet contains maximum 2 UID records

   ========================================================= */


/* =========================================================
   EXPERIMENT PARAMETERS
   ========================================================= */

#define SWARM_SIZE                  100

#define MEMORY_SIZE                 SWARM_SIZE

#define DETECTION_UID_LIMIT         100

#define SAME_THRESHOLD              10


/* =========================================================
   COMMUNICATION
   ========================================================= */

#define BROADCAST_INTERVAL_TICKS    8


/* =========================================================
   STARTUP
   ========================================================= */

#define STARTUP_FLASHES             5

#define FLASH_HALF_PERIOD_TICKS     8


/* =========================================================
   FLOODING
   ========================================================= */

#define FLOODING_MARKER             0xF1

#define MAX_RECORDS_PER_PACKET      2


/* =========================================================
   OPINION
   ========================================================= */

#define OPINION_B                   0

#define OPINION_A                   1


uint8_t opinion =
    OPINION_B;


/* =========================================================
   LOCAL COMPLETION
   ========================================================= */

uint8_t same_count =
    0;


/*
 * Reversible:
 *
 *      0 -> 1
 *      1 -> 0
 */

uint8_t s =
    0;


/* =========================================================
   META-COMPLETION
   ========================================================= */

/*
 * BLUE is latched.
 *
 * But algorithm continues after BLUE.
 */

uint8_t meta_completed =
    0;


/* =========================================================
   STARTUP
   ========================================================= */

uint8_t startup_finished =
    0;


uint8_t startup_phase =
    0;


uint32_t startup_last_tick =
    0;


/* =========================================================
   FLOODING RECORD
   ========================================================= */

typedef struct
{
    uint16_t uid;

    uint8_t state;

    uint8_t version;

} flooding_entry_t;


/* =========================================================
   MEMORY TABLE
   ========================================================= */

flooding_entry_t memory[
    MEMORY_SIZE
];


uint8_t memory_count =
    0;


/*
 * Version generated only by THIS UID.
 */

uint8_t own_version =
    0;


/*
 * Next table position to transmit.
 */

uint8_t tx_table_index =
    0;


/*
 * Number of valid records in current TX packet.
 */

uint8_t last_packet_record_count =
    0;


/* =========================================================
   TRANSMISSION
   ========================================================= */

message_t msg;


uint8_t tx_busy =
    0;


uint32_t last_broadcast_tick =
    0;


/* =========================================================
   VERSION COMPARISON
   ========================================================= */

uint8_t version_is_newer(
    uint8_t received_version,
    uint8_t stored_version
)
{
    uint8_t difference;


    difference =
        (uint8_t)
        (
            received_version
            -
            stored_version
        );


    if (
        difference
        ==
        0
    )
    {
        return 0;
    }


    if (
        difference
        <
        128
    )
    {
        return 1;
    }


    return 0;
}


/* =========================================================
   FIND UID
   ========================================================= */

int16_t find_uid(
    uint16_t uid
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
            memory[i].uid
            ==
            uid
        )
        {
            return
                (int16_t)i;
        }
    }


    return -1;
}


/* =========================================================
   INSERT NEW UID RECORD
   ========================================================= */

int16_t insert_new_record(
    uint16_t uid,
    uint8_t state,
    uint8_t version
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
        return -1;
    }


    /* Maximum 100 UIDs */

    if (
        memory_count
        >=
        MEMORY_SIZE
    )
    {
        return -1;
    }


    index =
        memory_count;


    memory[index].uid =
        uid;


    memory[index].state =
        state;


    memory[index].version =
        version;


    memory_count++;


    return
        (int16_t)index;
}


/* =========================================================
   MERGE RECEIVED RECORD
   ========================================================= */

void merge_flooding_record(
    uint16_t uid,
    uint8_t state,
    uint8_t version
)
{
    int16_t existing;


    /* Invalid state */

    if (
        state
        >
        1
    )
    {
        return;
    }


    /*
     * SELF is authoritative.
     *
     * Never overwrite our own state
     * using a network copy.
     */

    if (
        uid
        ==
        (uint16_t)kilo_uid
    )
    {
        return;
    }


    existing =
        find_uid(
            uid
        );


    /* =====================================================
       NEW UID
       ===================================================== */

    if (
        existing
        <
        0
    )
    {
        insert_new_record(

            uid,

            state,

            version
        );


        return;
    }


    /* =====================================================
       EXISTING UID

       Only replace if received version is newer.
       ===================================================== */

    if (
        version_is_newer(

            version,

            memory[
                (uint8_t)existing
            ].version
        )
    )
    {
        memory[
            (uint8_t)existing
        ].state =
            state;


        memory[
            (uint8_t)existing
        ].version =
            version;
    }
}


/* =========================================================
   INITIALISE TABLE
   ========================================================= */

void initialise_flooding_table(void)
{
    uint8_t i;


    for (
        i = 0;
        i < MEMORY_SIZE;
        i++
    )
    {
        memory[i].uid =
            0;


        memory[i].state =
            0;


        memory[i].version =
            0;
    }


    memory_count =
        0;


    own_version =
        0;


    tx_table_index =
        0;


    last_packet_record_count =
        0;


    /*
     * Every robot starts knowing itself.
     *
     * Initial:
     *
     *      s = 0
     *      version = 0
     */

    insert_new_record(

        (uint16_t)kilo_uid,

        s,

        own_version
    );
}


/* =========================================================
   UPDATE OWN UID RECORD

   CRITICAL:

   Whenever own s changes:

       state is updated immediately
       own_version++

   Example:

       s 0 -> 1:
           state = 1
           version++

       s 1 -> 0:
           state = 0
           version++

   ========================================================= */

void update_own_record(void)
{
    int16_t index;


    index =
        find_uid(
            (uint16_t)kilo_uid
        );


    /* Safety fallback */

    if (
        index
        <
        0
    )
    {
        insert_new_record(

            (uint16_t)kilo_uid,

            s,

            own_version
        );


        return;
    }


    /* =====================================================
       STATE CHANGED
       ===================================================== */

    if (
        memory[
            (uint8_t)index
        ].state
        !=
        s
    )
    {
        /*
         * Generate a newer version.
         */

        own_version++;


        /*
         * Update THIS UID's state.
         */

        memory[
            (uint8_t)index
        ].state =
            s;


        memory[
            (uint8_t)index
        ].version =
            own_version;
    }
}


/* =========================================================
   META-COMPLETION CHECK

   BLUE iff:

       own s == 1

       AND

       all required UIDs known

       AND

       all required UID states == 1

   ========================================================= */

void check_meta_completion(void)
{
    uint8_t i;


    /* =====================================================
       BLUE ALREADY LATCHED
       ===================================================== */

    if (
        meta_completed
    )
    {
        return;
    }


    /* =====================================================
       OWN TASK MUST BE COMPLETE
       ===================================================== */

    if (
        s
        !=
        1
    )
    {
        return;
    }


    /* =====================================================
       NEED ALL DISTINCT UIDs
       ===================================================== */

    if (
        memory_count
        <
        DETECTION_UID_LIMIT
    )
    {
        return;
    }


    /* =====================================================
       CHECK ALL REQUIRED STORED UIDs
       ===================================================== */

    for (
        i = 0;
        i < DETECTION_UID_LIMIT;
        i++
    )
    {
        if (
            memory[i].state
            !=
            1
        )
        {
            return;
        }
    }


    /* =====================================================
       META-COMPLETION DETECTED
       ===================================================== */

    meta_completed =
        1;
}


/* =========================================================
   LED
   ========================================================= */

void update_colour(void)
{
    if (
        !startup_finished
    )
    {
        return;
    }


    /* =====================================================
       BLUE
       ===================================================== */

    if (
        meta_completed
    )
    {
        set_color(
            RGB(0,0,3)
        );


        return;
    }


    /* =====================================================
       OPINION A
       ===================================================== */

    if (
        opinion
        ==
        OPINION_A
    )
    {
        set_color(
            RGB(0,3,0)
        );


        return;
    }


    /* =====================================================
       OPINION B
       ===================================================== */

    set_color(
        RGB(3,0,0)
    );
}


/* =========================================================
   BUILD FLOODING MESSAGE
   ========================================================= */

void build_flooding_message(void)
{
    uint8_t i;

    uint8_t header;

    uint8_t count;

    uint8_t first_index;

    uint8_t second_index;


    /* =====================================================
       CLEAR PACKET
       ===================================================== */

    for (
        i = 0;
        i < 9;
        i++
    )
    {
        msg.data[i] =
            0;
    }


    /* =====================================================
       PHYSICAL SENDER OPINION
       ===================================================== */

    msg.data[0] =
        opinion;


    /* =====================================================
       FLOODING MARKER
       ===================================================== */

    msg.data[8] =
        FLOODING_MARKER;


    /* =====================================================
       EMPTY TABLE SAFETY
       ===================================================== */

    if (
        memory_count
        ==
        0
    )
    {
        last_packet_record_count =
            0;


        msg.data[1] =
            0;


        msg.type =
            NORMAL;


        msg.crc =
            message_crc(
                &msg
            );


        return;
    }


    /* =====================================================
       WRAP CURSOR
       ===================================================== */

    if (
        tx_table_index
        >=
        memory_count
    )
    {
        tx_table_index =
            0;
    }


    first_index =
        tx_table_index;


    count =
        1;


    header =
        0;


    /* =====================================================
       RECORD 1
       ===================================================== */

    msg.data[2] =

        (uint8_t)
        (
            memory[
                first_index
            ].uid

            &

            0xFF
        );


    msg.data[3] =

        (uint8_t)
        (
            (
                memory[
                    first_index
                ].uid

                >>

                8
            )

            &

            0xFF
        );


    msg.data[4] =
        memory[
            first_index
        ].version;


    /* State 1 */

    if (
        memory[
            first_index
        ].state
        ==
        1
    )
    {
        header |=
            (1 << 2);
    }


    /* =====================================================
       RECORD 2
       ===================================================== */

    second_index =
        first_index
        +
        1;


    if (
        second_index
        <
        memory_count
    )
    {
        count =
            2;


        msg.data[5] =

            (uint8_t)
            (
                memory[
                    second_index
                ].uid

                &

                0xFF
            );


        msg.data[6] =

            (uint8_t)
            (
                (
                    memory[
                        second_index
                    ].uid

                    >>

                    8
                )

                &

                0xFF
            );


        msg.data[7] =
            memory[
                second_index
            ].version;


        /* State 2 */

        if (
            memory[
                second_index
            ].state
            ==
            1
        )
        {
            header |=
                (1 << 3);
        }
    }


    /* =====================================================
       RECORD COUNT
       ===================================================== */

    header |=
        (
            count
            &
            0x03
        );


    msg.data[1] =
        header;


    last_packet_record_count =
        count;


    msg.type =
        NORMAL;


    msg.crc =
        message_crc(
            &msg
        );
}


/* =========================================================
   TRANSMIT CALLBACK
   ========================================================= */

message_t *message_tx(void)
{
    if (
        !startup_finished
    )
    {
        return 0;
    }


    /*
     * No meta_completed check.
     *
     * BLUE robots continue transmitting.
     */

    if (
        tx_busy
    )
    {
        return
            &msg;
    }


    return 0;
}


/* =========================================================
   TX SUCCESS
   ========================================================= */

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


/* =========================================================
   COMMUNICATION STEP
   ========================================================= */

void communication_step(void)
{
    if (
        !startup_finished
    )
    {
        return;
    }


    /*
     * BLUE DOES NOT STOP COMMUNICATION.
     */


    if (
        tx_busy
    )
    {
        return;
    }


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


    /*
     * Make sure our current s/version
     * is in our memory table.
     */

    update_own_record();


    /*
     * Build packet from CURRENT table.
     */

    build_flooding_message();


    tx_busy =
        1;
}


/* =========================================================
   DIRECT VOTING
   ========================================================= */

void process_direct_opinion(
    uint8_t received_opinion
)
{
    /* =====================================================
       INVALID
       ===================================================== */

    if (
        received_opinion
        !=
        OPINION_A

        &&

        received_opinion
        !=
        OPINION_B
    )
    {
        return;
    }


    /* =====================================================
       SAME OPINION
       ===================================================== */

    if (
        received_opinion
        ==
        opinion
    )
    {
        if (
            same_count
            <
            SAME_THRESHOLD
        )
        {
            same_count++;
        }


        /* =================================================
           LOCAL COMPLETION
           ================================================= */

        if (
            same_count
            >=
            SAME_THRESHOLD
        )
        {
            same_count =
                SAME_THRESHOLD;


            /*
             * Only update when state actually changes.
             */

            if (
                s
                ==
                0
            )
            {
                s =
                    1;


                /*
                 * IMPORTANT:
                 *
                 * immediately update:
                 *
                 *      own memory state = 1
                 *      own version++
                 */

                update_own_record();
            }
        }


        return;
    }


    /* =====================================================
       DIFFERENT OPINION
       ===================================================== */

    /*
     * Adopt the received opinion.
     */

    opinion =
        received_opinion;


    /*
     * Stability sequence is broken.
     */

    same_count =
        0;


    /*
     * IMPORTANT:
     *
     * A different opinion means:
     *
     *      s = 0
     *
     * even if previously s == 1.
     */

    if (
        s
        !=
        0
    )
    {
        s =
            0;


        /*
         * CRITICAL:
         *
         * update THIS robot's UID record immediately:
         *
         *      state = 0
         *      version++
         *
         * The newer state=0 will then be flooded
         * to other robots.
         */

        update_own_record();
    }


    /*
     * Even when s was already zero,
     * keep own record synchronised.
     */

    else
    {
        update_own_record();
    }
}


/* =========================================================
   RECEIVE CALLBACK
   ========================================================= */

void message_rx(
    message_t *m,
    distance_measurement_t *d
)
{
    uint8_t received_opinion;

    uint8_t header;

    uint8_t record_count;


    (void)d;


    /* =====================================================
       NO RX DURING STARTUP
       ===================================================== */

    if (
        !startup_finished
    )
    {
        return;
    }


    /*
     * IMPORTANT:
     *
     * NO meta_completed check.
     *
     * BLUE robots continue:
     *
     *      RX
     *      voting
     *      s updates
     *      table updates
     */


    /* =====================================================
       CRC
       ===================================================== */

    if (
        message_crc(m)
        !=
        m->crc
    )
    {
        return;
    }


    if (
        m->type
        !=
        NORMAL
    )
    {
        return;
    }


    /* =====================================================
       DIRECT VOTING
       ===================================================== */

    received_opinion =
        m->data[0];


    process_direct_opinion(
        received_opinion
    );


    /* =====================================================
       FLOODING MARKER
       ===================================================== */

    if (
        m->data[8]
        !=
        FLOODING_MARKER
    )
    {
        return;
    }


    header =
        m->data[1];


    record_count =
        header
        &
        0x03;


    if (
        record_count
        >
        MAX_RECORDS_PER_PACKET
    )
    {
        return;
    }


    /* =====================================================
       RECORD 1
       ===================================================== */

    if (
        record_count
        >=
        1
    )
    {
        uint16_t uid1;

        uint8_t state1;

        uint8_t version1;


        uid1 =

            (uint16_t)
            m->data[2]

            |

            (
                (uint16_t)
                m->data[3]

                <<

                8
            );


        state1 =

            (
                header
                >>
                2
            )

            &

            0x01;


        version1 =
            m->data[4];


        merge_flooding_record(

            uid1,

            state1,

            version1
        );
    }


    /* =====================================================
       RECORD 2
       ===================================================== */

    if (
        record_count
        >=
        2
    )
    {
        uint16_t uid2;

        uint8_t state2;

        uint8_t version2;


        uid2 =

            (uint16_t)
            m->data[5]

            |

            (
                (uint16_t)
                m->data[6]

                <<

                8
            );


        state2 =

            (
                header
                >>
                3
            )

            &

            0x01;


        version2 =
            m->data[7];


        merge_flooding_record(

            uid2,

            state2,

            version2
        );
    }


    /* =====================================================
       SELF RECORD MUST ALWAYS MATCH CURRENT s
       ===================================================== */

    update_own_record();


    /* =====================================================
       CHECK ALL REQUIRED STATES
       ===================================================== */

    check_meta_completion();


    update_colour();
}


/* =========================================================
   STARTUP
   ========================================================= */

void startup_sequence(void)
{
    if (
        startup_finished
    )
    {
        return;
    }


    /* Stationary */

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


    /* =====================================================
       RED / OFF
       ===================================================== */

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


    /* =====================================================
       FORMAL t = 0
       ===================================================== */

    if (
        startup_phase
        >=
        STARTUP_FLASHES * 2
    )
    {
        /* Random opinion */

        if (
            rand()
            %
            2
        )
        {
            opinion =
                OPINION_A;
        }


        else
        {
            opinion =
                OPINION_B;
        }


        /* Local completion starts false */

        same_count =
            0;


        s =
            0;


        update_own_record();


        /* Flooding */

        tx_table_index =
            0;


        last_packet_record_count =
            0;


        tx_busy =
            0;


        startup_finished =
            1;


        last_broadcast_tick =
            kilo_ticks;


        set_motors(
            0,
            0
        );


        update_colour();
    }
}


/* =========================================================
   SETUP
   ========================================================= */

void setup(void)
{
    uint8_t seed;


    /* =====================================================
       NO MOVEMENT
       ===================================================== */

    set_motors(
        0,
        0
    );


    /* =====================================================
       RANDOM
       ===================================================== */

    seed =
        rand_hard();


    rand_seed(
        seed
    );


    srand(

        ((unsigned int)kilo_uid)

        ^

        (
            (unsigned int)seed
            <<
            8
        )
    );


    /* =====================================================
       TASK STATE
       ===================================================== */

    opinion =
        (uint8_t)(rand_soft() & 1U);


    same_count =
        0;


    s =
        0;


    meta_completed =
        0;


    /* =====================================================
       TABLE
       ===================================================== */

    initialise_flooding_table();


    /* =====================================================
       COMMUNICATION
       ===================================================== */

    tx_busy =
        0;


    last_broadcast_tick =
        kilo_ticks;


    build_flooding_message();


    /* =====================================================
       STARTUP
       ===================================================== */

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


/* =========================================================
   MAIN LOOP
   ========================================================= */

void loop(void)
{
    /* =====================================================
       ALWAYS STATIONARY
       ===================================================== */

    set_motors(
        0,
        0
    );


    /* =====================================================
       STARTUP
       ===================================================== */

    if (
        !startup_finished
    )
    {
        startup_sequence();


        return;
    }


    /* =====================================================
       KEEP OWN UID STATE CURRENT
       ===================================================== */

    update_own_record();


    /* =====================================================
       CHECK META-COMPLETION

       Requires:

           s == 1
           all 100 UIDs known
           all 100 states are 1
       ===================================================== */

    check_meta_completion();


    /* =====================================================
       LED
       ===================================================== */

    update_colour();


    /* =====================================================
       CONTINUE FLOODING

       INCLUDING AFTER BLUE.
       ===================================================== */

    communication_step();
}


/* =========================================================
   MAIN
   ========================================================= */

int main(void)
{
    kilo_init();


    kilo_message_rx =
        message_rx;


    kilo_message_tx =
        message_tx;


    kilo_message_tx_success =
        message_tx_success;


    kilo_start(
        setup,
        loop
    );


    return 0;
}
