#include "kilolib.h"
#include <stdlib.h>
#include <stdint.h>


/* =========================================================
   CENTRALISED BASELINE — VOTING ONLY

   STATIONARY + RATE-LIMITED COMMUNICATION VERSION
   =========================================================

   STARTUP:
       RED flashes 5 times.

       During startup:
           no communication
           no voting
           no movement

   FORMAL EXPERIMENT START:

       Random initial opinion:

           50% probability:
               A = GREEN

           50% probability:
               B = RED


   VOTING:

       Receive same opinion:
           keep current opinion

       Receive different opinion:
           adopt received opinion


   COMMUNICATION:

       Send ONLY own current opinion.

       data[0] = own opinion
       data[1..8] = 0

       Communication interval:

           8 ticks

       Same scheduling structure as
       Battery_LMC / Voting_LMC:

           wait 8 ticks
           prepare current message
           tx_busy = 1
           successful TX
           tx_busy = 0
           repeat


   IMPORTANT:

       No s.
       No same_count.
       No local completion detection.
       No meta-belief.
       No UID.
       No memory.
       No rebroadcast.
       No meta-consensus.
       No BLUE state.
       No automatic termination.


   LED:

       A = GREEN
       B = RED


   MOVEMENT:

       NONE.

       Robots remain stationary throughout
       the complete experiment.


   GLOBAL COMPLETION:

       Detected externally by camera /
       central observer.

       Experiment is terminated manually.

   ========================================================= */


/* =========================================================
   PARAMETERS
   ========================================================= */

#define OPINION_B                   0

#define OPINION_A                   1


/* =========================================================
   COMMUNICATION PARAMETERS
   ========================================================= */

#define BROADCAST_INTERVAL_TICKS    8


/* =========================================================
   STARTUP PARAMETERS
   ========================================================= */

#define STARTUP_FLASHES             5

#define FLASH_HALF_PERIOD_TICKS     8


/* =========================================================
   VOTING STATE
   ========================================================= */

uint8_t opinion =
    OPINION_B;


uint8_t received_opinion =
    OPINION_B;


/* =========================================================
   RECEIVE STATE
   ========================================================= */

uint8_t new_message =
    0;


/* =========================================================
   TRANSMISSION
   ========================================================= */

message_t msg;


/*
 * 1:
 *      packet prepared and waiting for successful TX
 *
 * 0:
 *      ready to schedule next packet
 */

uint8_t tx_busy =
    0;


/*
 * Last time a transmission was scheduled.
 */

uint32_t last_broadcast_tick =
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
   LED CONTROL
   ========================================================= */

/*
 * LED represents ONLY current opinion.
 *
 * A = GREEN
 * B = RED
 */

void update_colour(void)
{
    if (
        !startup_finished
    )
    {
        return;
    }


    /* =====================================================
       A = GREEN
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
       B = RED
       ===================================================== */

    set_color(
        RGB(3,0,0)
    );
}


/* =========================================================
   PREPARE MESSAGE
   ========================================================= */

/*
 * Send ONLY own current opinion.
 *
 * data[0] = opinion
 * data[1..8] = 0
 */

void prepare_message(void)
{
    uint8_t i;


    /* =====================================================
       CLEAR PAYLOAD
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
       CURRENT OWN OPINION
       ===================================================== */

    msg.data[0] =
        opinion;


    msg.type =
        NORMAL;


    msg.crc =
        message_crc(
            &msg
        );
}


/* =========================================================
   RECEIVE CALLBACK
   ========================================================= */

void message_rx(
    message_t *m,
    distance_measurement_t *d
)
{
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
       RECEIVE OPINION
       ===================================================== */

    received_opinion =
        m->data[0];


    /* =====================================================
       VALIDATE OPINION
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


    new_message =
        1;
}


/* =========================================================
   TRANSMIT CALLBACK
   ========================================================= */

/*
 * Same rate-limited mechanism as the
 * other physical experiments.
 */

message_t *message_tx(void)
{
    /* =====================================================
       NO TX DURING STARTUP
       ===================================================== */

    if (
        !startup_finished
    )
    {
        return 0;
    }


    /* =====================================================
       PACKET WAITING
       ===================================================== */

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
   TRANSMISSION SUCCESS CALLBACK
   ========================================================= */

void message_tx_success(void)
{
    /*
     * Current scheduled packet was
     * transmitted successfully.
     */

    tx_busy =
        0;
}


/* =========================================================
   COMMUNICATION STEP
   ========================================================= */

/*
 * Every 8 ticks:
 *
 *      if previous TX has completed:
 *
 *          prepare CURRENT opinion
 *          tx_busy = 1
 *
 *
 * This continues indefinitely.
 */

void communication_step(void)
{
    /* =====================================================
       NO COMMUNICATION DURING STARTUP
       ===================================================== */

    if (
        !startup_finished
    )
    {
        return;
    }


    /* =====================================================
       PREVIOUS TX STILL PENDING
       ===================================================== */

    if (
        tx_busy
    )
    {
        return;
    }


    /* =====================================================
       8-TICK RATE LIMIT
       ===================================================== */

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


    /* =====================================================
       PREPARE CURRENT OPINION
       ===================================================== */

    prepare_message();


    /* =====================================================
       REQUEST ONE TX
       ===================================================== */

    tx_busy =
        1;
}


/* =========================================================
   VOTING
   ========================================================= */

/*
 * If received opinion is different:
 *
 *      adopt received opinion.
 *
 * If same:
 *
 *      do nothing.
 */

void update_voting(void)
{
    if (
        received_opinion
        !=
        opinion
    )
    {
        opinion =
            received_opinion;


        /*
         * IMPORTANT:
         *
         * Do not modify an already pending packet.
         *
         * prepare_message() will put the latest
         * opinion into the NEXT scheduled TX.
         */
    }
}


/* =========================================================
   STARTUP SEQUENCE
   ========================================================= */

void startup_sequence(void)
{
    if (
        startup_finished
    )
    {
        return;
    }


    /* =====================================================
       ALWAYS STATIONARY
       ===================================================== */

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
       FIVE FLASHES FINISHED
       ===================================================== */

    if (
        startup_phase
        >=
        STARTUP_FLASHES * 2
    )
    {
        /* =================================================
           FORMAL EXPERIMENT t = 0

           Random initial opinion.
           ================================================= */

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


        received_opinion =
            opinion;


        new_message =
            0;


        tx_busy =
            0;


        /* =================================================
           FORMAL EXPERIMENT START
           ================================================= */

        startup_finished =
            1;


        /* =================================================
           START COMMUNICATION TIMER
           ================================================= */

        last_broadcast_tick =
            kilo_ticks;


        /* =================================================
           REMAIN STATIONARY
           ================================================= */

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
       RANDOM SEED
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
       INITIAL VOTING STATE
       ===================================================== */

    opinion =
        OPINION_B;


    received_opinion =
        OPINION_B;


    new_message =
        0;


    /* =====================================================
       TRANSMISSION
       ===================================================== */

    tx_busy =
        0;


    last_broadcast_tick =
        kilo_ticks;


    /*
     * Initial safety packet.
     *
     * Not sent before startup finishes.
     */

    prepare_message();


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

    startup_finished =
        0;


    startup_phase =
        0;


    startup_last_tick =
        kilo_ticks;


    /* =====================================================
       INITIAL RED
       ===================================================== */

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
       1. STARTUP
       ===================================================== */

    if (
        !startup_finished
    )
    {
        startup_sequence();


        return;
    }


    /* =====================================================
       2. VOTING
       ===================================================== */

    if (
        new_message
    )
    {
        update_voting();


        new_message =
            0;
    }


    /* =====================================================
       3. LED
       ===================================================== */

    update_colour();


    /* =====================================================
       4. RATE-LIMITED COMMUNICATION
       ===================================================== */

    communication_step();


    /* =====================================================
       NO TERMINATION
       =====================================================

       No local completion.
       No meta-completion.
       No BLUE.

       Robots remain stationary, communicate
       and vote indefinitely.

       Central observer determines when the
       global voting task has completed.
       ===================================================== */
}


/* =========================================================
   MAIN
   ========================================================= */

int main(void)
{
    kilo_init();


    /* =====================================================
       CALLBACKS
       ===================================================== */

    kilo_message_rx =
        message_rx;


    kilo_message_tx =
        message_tx;


    kilo_message_tx_success =
        message_tx_success;


    /* =====================================================
       START
       ===================================================== */

    kilo_start(
        setup,
        loop
    );


    return 0;
}