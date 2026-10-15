import numpy as np
import matplotlib.pyplot as plt
import json
import csv
from collections import deque
from pathlib import Path

# =========================================================
# GLOBAL SETTINGS
# =========================================================
NUM_ROUNDS = 700
NUM_REPETITIONS = 10

BATTERY_THRESHOLD = 100
CHARGE_PER_ROUND = 2.0

# Heterogeneous-charging panel
NUM_SLOW_AGENTS = 10
SLOW_CHARGE_PER_ROUND = 0.5


# =========================================================
# ID+R PARAMETERS
# =========================================================
IDR_MIN_BUFFER = 5
IDR_MEAN_TIMEOUT = 120.0
IDR_TAU = 1.0


# =========================================================
# ANONYMOUS PARAMETERS
# =========================================================
ANONYMOUS_MEMORY_MULTIPLIER = 1


# =========================================================
# LMC PARAMETERS
# =========================================================
K1 = 0.4
K2 = 0.57

LMC_DECISION_LEVEL = 0.99
LMC_CONFIRMATION_ROUNDS = 10


# =========================================================
# OUTPUT FILES
# =========================================================
# False redraws the figures from the saved .npz file and avoids repeating
# the approximately two-hour simulation.  If the file is absent, main()
# automatically performs the simulation once and saves it.
RUN_SIMULATION = False

OUTPUT_DIR = Path("outputs")
OUTPUT_DATA = OUTPUT_DIR / "lmc_initiating_simulation_results.npz"

OUTPUT_PNG = OUTPUT_DIR / "method_comparison.png"

OUTPUT_PDF = OUTPUT_DIR / "method_comparison.pdf"

PREMATURE_TRIAL_CSV = OUTPUT_DIR / "method_comparison_trial_events.csv"
PREMATURE_SUMMARY_CSV = OUTPUT_DIR / "method_comparison_premature_counts.csv"
PREMATURE_OUTPUT_PNG = OUTPUT_DIR / "supp_premature_counts.png"
PREMATURE_OUTPUT_PDF = OUTPUT_DIR / "supp_premature_counts.pdf"


# =========================================================
# EXPERIMENTS
# =========================================================
EXPERIMENTS = [

    # -----------------------------------------------------
    # A: N = 100
    # all robots +2 / round
    # -----------------------------------------------------
    {
        "panel": "A",

        "rows": 10,
        "columns": 10,

        "battery_seeds":
            list(range(12, 22)),

        "communication_seeds":
            list(range(1200, 1210)),

        "dropout": False,
    },


    # -----------------------------------------------------
    # B: N = 1000
    # 10 rows x 100 columns
    # -----------------------------------------------------
    {
        "panel": "B",

        "rows": 10,
        "columns": 100,

        "battery_seeds":
            list(range(12, 22)),

        "communication_seeds":
            list(range(1200, 1210)),

        "dropout": False,
    },


    # -----------------------------------------------------
    # C: heterogeneous charging
    #
    # 90 robots:
    #     +2 / round
    #
    # 10 robots:
    #     +0.5 / round
    # -----------------------------------------------------
    {
        "panel": "C",

        "rows": 10,
        "columns": 10,

        "battery_seeds":
            list(range(12, 22)),

        "communication_seeds":
            list(range(1200, 1210)),

        "dropout": False,

        "heterogeneous_charging": True,

        "num_slow_agents":
            NUM_SLOW_AGENTS,

        "slow_charge_per_round":
            SLOW_CHARGE_PER_ROUND,
    },
]


# =========================================================
# METHODS
# =========================================================
METHODS_NORMAL = [

    "Threshold",

    "Centralised controller",

    "Full-state flooding",

    "Anonymous Protocol",

    "Identity-Aware Protocol with Message Re-broadcasting (ID+R)",

    "Linear Meta-Completion (LMC)",
]


METHODS_DROPOUT = [

    "Threshold",

    "Fixed-membership centralised controller",

    "Full-state flooding",

    "Anonymous Protocol",

    "Identity-Aware Protocol with Message Re-broadcasting (ID+R)",

    "Linear Meta-Completion (LMC)",
]


# =========================================================
# PLOT STYLES
# =========================================================
STYLES = {

    "Threshold": {

        "color":
            "#ff7f0e",

        "linestyle":
            "-",

        "marker":
            "s",

        "markevery":
            (0, 25),
    },


    "Anonymous Protocol": {

        "color":
            "#d62728",

        "linestyle":
            "-",

        "marker":
            "D",

        "markevery":
            (5, 25),
    },


    "Centralised controller": {

        "color":
            "#9467bd",

        "linestyle":
            "--",

        "marker":
            "X",

        "markevery":
            (10, 25),
    },


    "Fixed-membership centralised controller": {

        "color":
            "#9467bd",

        "linestyle":
            "--",

        "marker":
            "X",

        "markevery":
            (10, 25),
    },


    "Identity-Aware Protocol with Message Re-broadcasting (ID+R)": {

        "color":
            "#8c564b",

        "linestyle":
            "-.",

        "marker":
            "v",

        "markevery":
            (15, 25),
    },


    "Full-state flooding": {

        "color":
            "#2ca02c",

        "linestyle":
            "--",

        "marker":
            "o",

        "markevery":
            (18, 25),
    },


    "Linear Meta-Completion (LMC)": {

        "color":
            "#111111",

        "linestyle":
            ":",

        "marker":
            "P",

        "markevery":
            (20, 25),
    },
}


# Concise labels prevent the shared legend from overlapping at journal width.
DISPLAY_NAMES = {
    "Threshold": "Threshold",
    "Centralised controller": "Centralised",
    "Fixed-membership centralised controller": "Centralised",
    "Full-state flooding": "Flooding",
    "Anonymous Protocol": "Anonymous",
    "Identity-Aware Protocol with Message Re-broadcasting (ID+R)": "ID+R",
    "Linear Meta-Completion (LMC)": "LMC",
}


# =========================================================
# FIXED ORTHOGONAL GRID
# =========================================================
def orthogonal_neighbors(
    agent_id,
    rows,
    columns,
    active_mask,
):

    row = (
        agent_id
        //
        columns
    )

    col = (
        agent_id
        %
        columns
    )

    neighbors = []


    # UP
    if row > 0:

        neighbors.append(
            agent_id
            -
            columns
        )


    # DOWN
    if row < rows - 1:

        neighbors.append(
            agent_id
            +
            columns
        )


    # LEFT
    if col > 0:

        neighbors.append(
            agent_id
            -
            1
        )


    # RIGHT
    if col < columns - 1:

        neighbors.append(
            agent_id
            +
            1
        )


    return [

        int(neighbor)

        for neighbor
        in neighbors

        if active_mask[
            neighbor
        ]
    ]


# =========================================================
# RANDOM ORTHOGONAL NEIGHBOUR
# =========================================================
def random_orthogonal_neighbor(
    agent_id,
    rows,
    columns,
    active_mask,
    rng,
):

    candidates = (
        orthogonal_neighbors(

            agent_id,

            rows,

            columns,

            active_mask,
        )
    )


    if not candidates:

        return None


    return int(
        rng.choice(
            candidates
        )
    )


# =========================================================
# BATTERY HISTORY
# =========================================================
def build_battery_history(
    config,
    battery_seed,
):

    num_agents = (

        config[
            "rows"
        ]

        *

        config[
            "columns"
        ]
    )


    rounds = np.arange(

        NUM_ROUNDS
        +
        1,

        dtype=float,
    )


    rng = np.random.Generator(

        np.random.PCG64(
            battery_seed
        )
    )


    # -----------------------------------------------------
    # Initial battery:
    #
    # uniform integer 0 ... 100
    # -----------------------------------------------------
    initial_batteries = (

        rng.integers(

            0,

            BATTERY_THRESHOLD
            +
            1,

            size=num_agents,

            dtype=np.int16,
        )

        .astype(
            float
        )
    )


    # -----------------------------------------------------
    # Default:
    #
    # all robots +2 / round
    # -----------------------------------------------------
    charge_rates = np.full(

        num_agents,

        CHARGE_PER_ROUND,

        dtype=float,
    )


    # -----------------------------------------------------
    # PANEL D
    #
    # 90 robots:
    #     +2 / round
    #
    # 10 robots:
    #     +0.5 / round
    #
    # The 10 slow robots are selected randomly
    # but reproducibly for each seed.
    # -----------------------------------------------------
    if config.get(
        "heterogeneous_charging",
        False,
    ):

        num_slow_agents = int(

            config.get(
                "num_slow_agents",
                NUM_SLOW_AGENTS,
            )
        )


        slow_charge_per_round = float(

            config.get(
                "slow_charge_per_round",
                SLOW_CHARGE_PER_ROUND,
            )
        )


        if (

            num_slow_agents
            <
            0

            or

            num_slow_agents
            >
            num_agents

        ):

            raise ValueError(
                "num_slow_agents must be between "
                "0 and num_agents."
            )


        # -------------------------------------------------
        # Separate RNG:
        #
        # keeps original battery initialization unchanged.
        # -------------------------------------------------
        slow_rng = np.random.default_rng(

            battery_seed
            +
            900000
        )


        slow_agent_ids = np.sort(

            slow_rng.choice(

                num_agents,

                size=
                    num_slow_agents,

                replace=
                    False,
            )
        )


        charge_rates[
            slow_agent_ids
        ] = (
            slow_charge_per_round
        )


        print(

            f"Panel "
            f"{config['panel']} "
            f"slow agents "
            f"(+{slow_charge_per_round}/round): "
            f"{slow_agent_ids.tolist()}"
        )


    # -----------------------------------------------------
    # battery_i(t)
    #
    # =
    #
    # min(
    #     initial_i + rate_i * t,
    #     100
    # )
    # -----------------------------------------------------
    battery_history = np.minimum(

        initial_batteries[
            :,
            np.newaxis,
        ]

        +

        charge_rates[
            :,
            np.newaxis,
        ]

        *

        rounds[
            np.newaxis,
            :
        ],

        BATTERY_THRESHOLD,

    ).astype(
        float
    )


    # -----------------------------------------------------
    # Permanent dropout
    #
    # Failed robot freezes before failure round.
    # -----------------------------------------------------
    if config[
        "dropout"
    ]:

        failure_round = (
            config[
                "failure_round"
            ]
        )


        for failed_id in (
            config[
                "failed_agent_ids"
            ]
        ):

            frozen_battery = (

                battery_history[
                    failed_id,
                    failure_round - 1,
                ]
            )


            battery_history[
                failed_id,
                failure_round:
            ] = (
                frozen_battery
            )


    return battery_history


# =========================================================
# ANONYMOUS
# =========================================================
def anonymous_add_state(
    memory,
    state,
    capacity,
):

    if len(memory) >= capacity:

        memory.popleft()


    memory.append(
        int(state)
    )


# =========================================================
# ID+R STORAGE
# =========================================================
def create_idr_storage(
    num_agents,
):

    memories = [

        {}

        for _ in range(
            num_agents
        )
    ]


    queues = [

        deque()

        for _ in range(
            num_agents
        )
    ]


    queued_sets = [

        set()

        for _ in range(
            num_agents
        )
    ]


    return (
        memories,
        queues,
        queued_sets,
    )


# =========================================================
# ID+R TIMEOUT
# =========================================================
def sample_idr_timeout(
    rng,
):

    return max(

        1,

        int(

            np.ceil(

                rng.exponential(
                    IDR_MEAN_TIMEOUT
                )
            )
        )
    )


# =========================================================
# ID+R REMOVE EXPIRED
# =========================================================
def idr_remove_expired(
    memory,
    queue,
    queued_set,
    current_round,
):

    expired = {

        uid

        for uid, record
        in memory.items()

        if current_round
        >=
        record[
            "expiry"
        ]
    }


    if not expired:

        return


    for uid in expired:

        del memory[
            uid
        ]


    new_queue = deque()

    new_set = set()


    while queue:

        uid = (
            queue.popleft()
        )


        if uid in expired:

            continue


        if uid not in memory:

            continue


        if uid in new_set:

            continue


        new_queue.append(
            uid
        )


        new_set.add(
            uid
        )


    queue.extend(
        new_queue
    )


    queued_set.clear()


    queued_set.update(
        new_set
    )


# =========================================================
# ID+R RECEIVE
# =========================================================
def idr_receive(
    memory,
    queue,
    queued_set,
    self_uid,
    source_uid,
    source_state,
    current_round,
    timeout_rng,
):

    source_uid = int(
        source_uid
    )


    source_state = int(
        source_state
    )


    # -----------------------------------------------------
    # SELF is not stored in ID+R buffer.
    # -----------------------------------------------------
    if source_uid == self_uid:

        return


    existing = (
        memory.get(
            source_uid
        )
    )


    # -----------------------------------------------------
    # New UID
    # -----------------------------------------------------
    if existing is None:

        memory[
            source_uid
        ] = {

            "state":
                source_state,

            "expiry":

                current_round

                +

                sample_idr_timeout(
                    timeout_rng
                ),
        }


        if (
            source_uid
            not in
            queued_set
        ):

            queue.append(
                source_uid
            )


            queued_set.add(
                source_uid
            )


        return


    # -----------------------------------------------------
    # Same UID + same state:
    #
    # discard
    #
    # timeout NOT refreshed
    # -----------------------------------------------------
    if (

        existing[
            "state"
        ]

        ==

        source_state

    ):

        return


    # -----------------------------------------------------
    # State changed:
    #
    # replace + new timeout
    # -----------------------------------------------------
    memory[
        source_uid
    ] = {

        "state":
            source_state,

        "expiry":

            current_round

            +

            sample_idr_timeout(
                timeout_rng
            ),
    }


    if (
        source_uid
        not in
        queued_set
    ):

        queue.append(
            source_uid
        )


        queued_set.add(
            source_uid
        )


# =========================================================
# ID+R DECISION
# =========================================================
def idr_complete(
    memory,
    own_state,
):

    # Own-state veto
    if own_state != 1:

        return False


    # Minimum buffer
    if (
        len(memory)
        <
        IDR_MIN_BUFFER
    ):

        return False


    # Entire current buffer
    completed_count = sum(

        record[
            "state"
        ]

        for record
        in memory.values()
    )


    return (

        completed_count

        >=

        IDR_TAU
        *
        len(memory)
    )


# =========================================================
# ID+R COMMUNICATION
# =========================================================
def idr_communication_round(
    memories,
    queues,
    queued_sets,
    active_mask,
    current_states,
    communication_rng,
    timeout_rng,
    current_round,
    rows,
    columns,
):

    num_agents = len(
        memories
    )


    # -----------------------------------------------------
    # Expire old records.
    # -----------------------------------------------------
    for agent_id in np.flatnonzero(
        active_mask
    ):

        idr_remove_expired(

            memories[
                agent_id
            ],

            queues[
                agent_id
            ],

            queued_sets[
                agent_id
            ],

            current_round,
        )


    # -----------------------------------------------------
    # Synchronous outgoing packets.
    # -----------------------------------------------------
    outgoing = [

        None

        for _ in range(
            num_agents
        )
    ]


    for sender in np.flatnonzero(
        active_mask
    ):

        packet = None


        while (

            queues[
                sender
            ]

            and

            packet is None

        ):

            source_uid = int(

                queues[
                    sender
                ].popleft()
            )


            queued_sets[
                sender
            ].discard(
                source_uid
            )


            record = (
                memories[
                    sender
                ].get(
                    source_uid
                )
            )


            if record is not None:

                packet = (

                    source_uid,

                    int(
                        record[
                            "state"
                        ]
                    ),
                )


        # -------------------------------------------------
        # If no rebroadcast pending:
        #
        # send own state.
        # -------------------------------------------------
        if packet is None:

            packet = (

                int(sender),

                int(
                    current_states[
                        sender
                    ]
                ),
            )


        outgoing[
            sender
        ] = packet


    deliveries = []


    for sender in np.flatnonzero(
        active_mask
    ):

        receiver = (
            random_orthogonal_neighbor(

                sender,

                rows,

                columns,

                active_mask,

                communication_rng,
            )
        )


        if receiver is None:

            continue


        (
            source_uid,
            source_state,
        ) = outgoing[
            sender
        ]


        deliveries.append(

            (
                receiver,

                source_uid,

                source_state,
            )
        )


    for (
        receiver,
        source_uid,
        source_state,
    ) in deliveries:

        idr_receive(

            memories[
                receiver
            ],

            queues[
                receiver
            ],

            queued_sets[
                receiver
            ],

            receiver,

            source_uid,

            source_state,

            current_round,

            timeout_rng,
        )


# =========================================================
# JULIAN-STYLE FULL-TABLE FLOODING
# =========================================================
def create_flooding_storage(
    num_agents,
    initial_states,
):

    tables = []


    for agent_id in range(
        num_agents
    ):

        table = {

            int(
                agent_id
            ):
            (
                int(
                    initial_states[
                        agent_id
                    ]
                ),

                0,
            )
        }


        tables.append(
            table
        )


    return tables


# =========================================================
# FLOODING OWN STATE UPDATE
# =========================================================
def flooding_update_own_state(
    table,
    agent_id,
    current_state,
    previous_state,
    current_round,
):

    if (

        int(
            current_state
        )

        !=

        int(
            previous_state
        )

    ):

        table[
            int(agent_id)
        ] = (

            int(
                current_state
            ),

            int(
                current_round
            ),
        )


# =========================================================
# FLOODING MERGE
# =========================================================
def flooding_merge_table(
    receiver_table,
    sender_table,
):

    for (
        uid,
        (
            state,
            timestamp,
        ),
    ) in sender_table.items():

        existing = (
            receiver_table.get(
                uid
            )
        )


        # -------------------------------------------------
        # Unknown UID
        # -------------------------------------------------
        if existing is None:

            receiver_table[
                int(uid)
            ] = (

                int(state),

                int(timestamp),
            )


            continue


        # -------------------------------------------------
        # Keep newest information.
        # -------------------------------------------------
        existing_timestamp = (
            existing[
                1
            ]
        )


        if (

            int(
                timestamp
            )

            >

            int(
                existing_timestamp
            )

        ):

            receiver_table[
                int(uid)
            ] = (

                int(state),

                int(timestamp),
            )


# =========================================================
# FLOODING COMMUNICATION
# =========================================================
def flooding_communication_round(
    tables,
    active_mask,
    neighbor_lists,
):

    # -----------------------------------------------------
    # Snapshot:
    #
    # information travels at most one grid hop
    # per simulation round.
    # -----------------------------------------------------
    snapshots = [

        dict(
            table
        )

        for table
        in tables
    ]


    # -----------------------------------------------------
    # Every active robot broadcasts ENTIRE table
    # to ALL active orthogonal neighbours.
    # Merge directly from the fixed snapshots instead of
    # first constructing a large duplicate delivery list.
    # -----------------------------------------------------
    for sender in np.flatnonzero(
        active_mask
    ):

        for receiver in neighbor_lists[int(sender)]:
            if active_mask[receiver]:
                flooding_merge_table(
                    tables[int(receiver)],
                    snapshots[int(sender)],
                )


# =========================================================
# FLOODING COMPLETION
# =========================================================
def flooding_complete(
    table,
    num_agents,
    own_state,
):

    # Own-state veto
    if (
        int(
            own_state
        )
        !=
        1
    ):

        return False


    # Must know all N UIDs
    if (
        len(table)
        !=
        num_agents
    ):

        return False


    # All latest states must be 1
    return all(

        int(
            state
        )
        ==
        1

        for (
            state,
            timestamp,
        )
        in table.values()
    )


# =========================================================
# ONE SIMULATION RUN
# =========================================================
def run_once(
    config,
    battery_seed,
    communication_seed,
):

    rows = (
        config[
            "rows"
        ]
    )


    columns = (
        config[
            "columns"
        ]
    )


    num_agents = (
        rows
        *
        columns
    )

    # The grid geometry is fixed, so calculate its orthogonal topology once
    # instead of rebuilding the same neighbor lists in every flooding round.
    all_active = np.ones(num_agents, dtype=bool)
    grid_neighbor_lists = [
        orthogonal_neighbors(agent_id, rows, columns, all_active)
        for agent_id in range(num_agents)
    ]


    dropout = (
        config[
            "dropout"
        ]
    )


    methods = (

        METHODS_DROPOUT

        if dropout

        else

        METHODS_NORMAL
    )


    # =====================================================
    # RNG
    # =====================================================
    rng_idr = (
        np.random.default_rng(
            communication_seed
        )
    )


    rng_timeout = (
        np.random.default_rng(

            communication_seed
            +
            50000
        )
    )


    rng_anonymous = (
        np.random.default_rng(

            communication_seed
            +
            100000
        )
    )


    rng_lmc = (
        np.random.default_rng(

            communication_seed
            +
            200000
        )
    )


    # =====================================================
    # BATTERY
    # =====================================================
    battery_history = (
        build_battery_history(

            config,

            battery_seed,
        )
    )


    completion_history = (

        battery_history

        >=

        BATTERY_THRESHOLD

    ).astype(
        np.uint8
    )


    # =====================================================
    # ACTIVE MEMBERSHIP
    # =====================================================
    active_history = np.ones(

        (
            num_agents,
            NUM_ROUNDS + 1,
        ),

        dtype=bool,
    )


    if dropout:

        failure_round = (
            config[
                "failure_round"
            ]
        )


        failed_ids = (
            config[
                "failed_agent_ids"
            ]
        )


        active_history[
            failed_ids,
            failure_round:
        ] = False


        if np.any(

            completion_history[
                failed_ids,
                failure_round,
            ]

            ==
            1
        ):

            raise RuntimeError(

                f"Battery seed "
                f"{battery_seed}: "
                "failed robot completed "
                "before dropout."
            )


    # =====================================================
    # TRUE COMPLETION
    #
    # Dropout:
    #
    # all surviving active robots.
    # =====================================================
    true_completion = np.zeros(

        NUM_ROUNDS
        +
        1,

        dtype=bool,
    )


    for round_index in range(

        NUM_ROUNDS
        +
        1
    ):

        active_mask = (
            active_history[
                :,
                round_index
            ]
        )


        true_completion[
            round_index
        ] = np.all(

            completion_history[
                active_mask,
                round_index,
            ]

            ==
            1
        )


    completion_candidates = (
        np.flatnonzero(
            true_completion
        )
    )


    if (
        completion_candidates.size
        ==
        0
    ):

        raise RuntimeError(
            "Active swarm did not complete "
            "within NUM_ROUNDS."
        )


    true_completion_round = int(

        completion_candidates[
            0
        ]
    )


    # =====================================================
    # TRANSITION FLAGS
    # =====================================================
    threshold_transitioned = np.zeros(
        num_agents,
        dtype=bool,
    )


    anonymous_transitioned = np.zeros(
        num_agents,
        dtype=bool,
    )


    centralized_transitioned = np.zeros(
        num_agents,
        dtype=bool,
    )


    idr_transitioned = np.zeros(
        num_agents,
        dtype=bool,
    )


    flooding_transitioned = np.zeros(
        num_agents,
        dtype=bool,
    )


    lmc_transitioned = np.zeros(
        num_agents,
        dtype=bool,
    )


    # =====================================================
    # ANONYMOUS
    # =====================================================
    anonymous_capacity = int(

        ANONYMOUS_MEMORY_MULTIPLIER

        *

        num_agents
    )


    anonymous_memories = [

        deque(
            maxlen=
                anonymous_capacity
        )

        for _ in range(
            num_agents
        )
    ]


    # =====================================================
    # ID+R
    # =====================================================
    (
        idr_memories,
        idr_queues,
        idr_sets,
    ) = create_idr_storage(
        num_agents
    )


    # =====================================================
    # FLOODING
    # =====================================================
    initial_states = (
        completion_history[
            :,
            0
        ]
    )


    flooding_tables = (
        create_flooding_storage(

            num_agents,

            initial_states,
        )
    )


    # =====================================================
    # LMC
    # =====================================================
    lmc_belief = np.zeros(
        num_agents,
        dtype=float,
    )


    lmc_confirmation_counter = np.zeros(

        num_agents,

        dtype=np.int16,
    )


    # =====================================================
    # RESULTS
    # =====================================================
    results = {

        method_name:
            np.zeros(
                NUM_ROUNDS
                +
                1
            )

        for method_name
        in methods
    }


    # =====================================================
    # RECORD RESULTS
    # =====================================================
    def record_results(
        round_index
    ):

        active_mask = (
            active_history[
                :,
                round_index
            ]
        )


        results[
            "Threshold"
        ][
            round_index
        ] = np.mean(

            threshold_transitioned[
                active_mask
            ]
        )


        results[
            "Anonymous Protocol"
        ][
            round_index
        ] = np.mean(

            anonymous_transitioned[
                active_mask
            ]
        )


        if dropout:

            results[
                "Fixed-membership centralised controller"
            ][
                round_index
            ] = np.mean(

                centralized_transitioned[
                    active_mask
                ]
            )


        else:

            results[
                "Centralised controller"
            ][
                round_index
            ] = np.mean(

                centralized_transitioned
            )


        results[
            "Identity-Aware Protocol with Message Re-broadcasting (ID+R)"
        ][
            round_index
        ] = np.mean(

            idr_transitioned[
                active_mask
            ]
        )


        results[
            "Full-state flooding"
        ][
            round_index
        ] = np.mean(

            flooding_transitioned[
                active_mask
            ]
        )


        results[
            "Linear Meta-Completion (LMC)"
        ][
            round_index
        ] = np.mean(

            lmc_transitioned[
                active_mask
            ]
        )


    # =====================================================
    # ROUND ZERO
    # =====================================================
    threshold_transitioned |= (

        initial_states
        ==
        1
    )


    if np.all(
        initial_states
        ==
        1
    ):

        centralized_transitioned[
            :
        ] = True


    record_results(
        0
    )


    # =====================================================
    # MAIN LOOP
    # =====================================================
    for round_index in range(

        1,

        NUM_ROUNDS
        +
        1
    ):

        active_mask = (
            active_history[
                :,
                round_index
            ]
        )


        current_states = (
            completion_history[
                :,
                round_index
            ]
        )


        previous_states = (
            completion_history[
                :,
                round_index
                -
                1
            ]
        )


        # =================================================
        # 1. BATTERY THRESHOLD
        # =================================================
        threshold_transitioned |= (

            active_mask

            &

            (
                current_states
                ==
                1
            )
        )


        # =================================================
        # 2. ANONYMOUS PROTOCOL
        # =================================================
        for agent_id in np.flatnonzero(
            active_mask
        ):

            if (
                anonymous_transitioned[
                    agent_id
                ]
            ):

                continue


            neighbor = (
                random_orthogonal_neighbor(

                    agent_id,

                    rows,

                    columns,

                    active_mask,

                    rng_anonymous,
                )
            )


            if neighbor is None:

                continue


            anonymous_add_state(

                anonymous_memories[
                    agent_id
                ],

                current_states[
                    neighbor
                ],

                anonymous_capacity,
            )


            memory = (
                anonymous_memories[
                    agent_id
                ]
            )


            if (

                len(memory)
                ==
                anonymous_capacity

                and

                all(
                    state == 1
                    for state
                    in memory
                )
            ):

                anonymous_transitioned[
                    agent_id
                ] = True


        # =================================================
        # 3. CENTRALISED CONTROLLER
        # =================================================
        if not dropout:

            if np.all(
                current_states
                ==
                1
            ):

                centralized_transitioned[
                    :
                ] = True


        else:

            # -------------------------------------------------
            # Fixed original membership.
            #
            # After dropout, complete reporting becomes
            # impossible.
            # -------------------------------------------------
            if (

                np.all(
                    active_mask
                )

                and

                np.all(
                    current_states
                    ==
                    1
                )
            ):

                centralized_transitioned[
                    :
                ] = True


        # =================================================
        # 4. ID+R
        # =================================================
        if not np.all(idr_transitioned[active_mask]):
            idr_communication_round(
                idr_memories,
                idr_queues,
                idr_sets,
                active_mask,
                current_states,
                rng_idr,
                rng_timeout,
                round_index,
                rows,
                columns,
            )


        for agent_id in np.flatnonzero(
            active_mask
        ):

            if (
                idr_transitioned[
                    agent_id
                ]
            ):

                continue


            if idr_complete(

                idr_memories[
                    agent_id
                ],

                current_states[
                    agent_id
                ],
            ):

                idr_transitioned[
                    agent_id
                ] = True


        # =================================================
        # 5. FULL-TABLE FLOODING
        # =================================================

        # -------------------------------------------------
        # Update authoritative own entry.
        # -------------------------------------------------
        for agent_id in np.flatnonzero(
            active_mask
        ):

            flooding_update_own_state(

                flooding_tables[
                    agent_id
                ],

                agent_id,

                current_states[
                    agent_id
                ],

                previous_states[
                    agent_id
                ],

                round_index,
            )


        # -------------------------------------------------
        # Entire table to all orthogonal neighbours.
        # -------------------------------------------------
        # Transition flags are irreversible.  Once every active robot has
        # transitioned, further full-table propagation cannot alter a curve.
        if not np.all(flooding_transitioned[active_mask]):
            flooding_communication_round(
                flooding_tables,
                active_mask,
                grid_neighbor_lists,
            )


        # -------------------------------------------------
        # Exact completion.
        # -------------------------------------------------
        for agent_id in np.flatnonzero(
            active_mask
        ):

            if (
                flooding_transitioned[
                    agent_id
                ]
            ):

                continue


            if flooding_complete(

                flooding_tables[
                    agent_id
                ],

                num_agents,

                current_states[
                    agent_id
                ],
            ):

                flooding_transitioned[
                    agent_id
                ] = True


        # =================================================
        # 6. LINEAR META-COMPLETION (LMC)
        # =================================================
        previous_belief = (
            lmc_belief.copy()
        )


        if dropout:

            lmc_belief[
                ~active_mask
            ] = 0.0


        for agent_id in np.flatnonzero(
            active_mask
        ):

            # ---------------------------------------------
            # Own state veto.
            # ---------------------------------------------
            if (
                current_states[
                    agent_id
                ]
                ==
                0
            ):

                lmc_belief[
                    agent_id
                ] = 0.0


                continue


            neighbor = (
                random_orthogonal_neighbor(

                    agent_id,

                    rows,

                    columns,

                    active_mask,

                    rng_lmc,
                )
            )


            if neighbor is None:

                lmc_belief[
                    agent_id
                ] = 0.0


                continue


            lmc_belief[
                agent_id
            ] = (

                K1
                *
                previous_belief[
                    agent_id
                ]

                +

                K2
                *
                previous_belief[
                    neighbor
                ]

                +

                (
                    1.0
                    -
                    K1
                    -
                    K2
                )
            )


        # =================================================
        # LMC CONFIRMATION
        # =================================================
        lmc_above_threshold = (

            active_mask

            &

            (
                lmc_belief
                >=
                LMC_DECISION_LEVEL
            )
        )


        lmc_confirmation_counter = np.where(

            lmc_above_threshold,

            lmc_confirmation_counter
            +
            1,

            0,
        )


        lmc_transitioned |= (

            active_mask

            &

            (
                lmc_confirmation_counter

                >=

                LMC_CONFIRMATION_ROUNDS
            )
        )


        # =================================================
        # RECORD
        # =================================================
        record_results(
            round_index
        )


    # =====================================================
    # DIAGNOSTICS
    # =====================================================
    final_active_mask = (
        active_history[
            :,
            NUM_ROUNDS
        ]
    )


    final_active_ids = (
        np.flatnonzero(
            final_active_mask
        )
    )


    idr_buffer_sizes = np.array(

        [

            len(
                idr_memories[
                    agent_id
                ]
            )

            for agent_id
            in final_active_ids
        ]
    )


    flooding_table_sizes = np.array(

        [

            len(
                flooding_tables[
                    agent_id
                ]
            )

            for agent_id
            in final_active_ids
        ]
    )


    flooding_completed_counts = np.array(

        [

            sum(

                int(state)
                ==
                1

                for (
                    state,
                    timestamp,
                )
                in flooding_tables[
                    agent_id
                ].values()
            )

            for agent_id
            in final_active_ids
        ]
    )


    print()


    print(

        f"Panel "
        f"{config['panel']} "
        f"| N={num_agents}"
    )


    print(

        f"True completion round: "
        f"{true_completion_round}"
    )


    print(

        "ID+R final buffer size: "
        f"min={idr_buffer_sizes.min()}, "
        f"mean={idr_buffer_sizes.mean():.2f}, "
        f"max={idr_buffer_sizes.max()}"
    )


    print(

        "Flooding final known identities: "
        f"min={flooding_table_sizes.min()}, "
        f"mean={flooding_table_sizes.mean():.2f}, "
        f"max={flooding_table_sizes.max()}"
    )


    print(

        "Flooding final known completed states: "
        f"min={flooding_completed_counts.min()}, "
        f"mean={flooding_completed_counts.mean():.2f}, "
        f"max={flooding_completed_counts.max()}"
    )


    print()


    return {

        "results":
            results,

        "true_completion_round":
            true_completion_round,
    }


# =========================================================
# TEN-SEED MEAN
# =========================================================
def run_experiment(
    config
):

    all_results = []

    completion_rounds = []


    for run_index, (
        battery_seed,
        communication_seed,
    ) in enumerate(

        zip(

            config[
                "battery_seeds"
            ],

            config[
                "communication_seeds"
            ],
        ),

        start=1,
    ):

        print(
            "="
            *
            70
        )


        print(

            f"Panel "
            f"{config['panel']}, "
            f"run "
            f"{run_index:2d}/"
            f"{NUM_REPETITIONS}: "
            f"battery_seed="
            f"{battery_seed}, "
            f"communication_seed="
            f"{communication_seed}"
        )


        run_result = (
            run_once(

                config,

                battery_seed,

                communication_seed,
            )
        )


        all_results.append(

            run_result[
                "results"
            ]
        )


        completion_rounds.append(

            run_result[
                "true_completion_round"
            ]
        )


    methods = (

        METHODS_DROPOUT

        if config[
            "dropout"
        ]

        else

        METHODS_NORMAL
    )


    mean_results = {}


    for method_name in methods:

        stacked = np.stack(

            [

                result[
                    method_name
                ]

                for result
                in all_results
            ],

            axis=0,
        )


        mean_results[
            method_name
        ] = np.mean(

            stacked,

            axis=0,
        )


    print(
        "="
        *
        70
    )


    print(

        f"Panel "
        f"{config['panel']} "
        f"completion rounds: "
        f"{completion_rounds}"
    )


    print(

        f"Panel "
        f"{config['panel']} "
        f"completion range: "
        f"{min(completion_rounds)}"
        f"–"
        f"{max(completion_rounds)}"
    )


    print(
        "="
        *
        70
    )


    return {

        "config":
            config,

        "methods":
            methods,

        "mean_results":
            mean_results,

        "all_results":
            all_results,

        "completion_rounds":
            completion_rounds,
    }


# =========================================================
# SAVE / LOAD CALCULATED DATA
# Set RUN_SIMULATION=False after one completed run to redraw
# the figure without repeating the simulations.
# =========================================================
def save_experiments(
    experiments,
    output_path=OUTPUT_DATA,
):

    method_names = list(dict.fromkeys(
        method_name
        for experiment in experiments
        for method_name in experiment["methods"]
    ))

    num_panels = len(experiments)
    num_methods = len(method_names)
    num_repetitions = max(
        len(experiment["all_results"])
        for experiment in experiments
    )

    mean_curves = np.full(
        (num_panels, num_methods, NUM_ROUNDS + 1),
        np.nan,
        dtype=float,
    )

    repetition_curves = np.full(
        (
            num_panels,
            num_repetitions,
            num_methods,
            NUM_ROUNDS + 1,
        ),
        np.nan,
        dtype=float,
    )

    method_present = np.zeros(
        (num_panels, num_methods),
        dtype=bool,
    )

    completion_rounds = np.full(
        (num_panels, num_repetitions),
        -1,
        dtype=np.int32,
    )

    for panel_index, experiment in enumerate(experiments):

        for method_name in experiment["methods"]:

            method_index = method_names.index(method_name)
            method_present[panel_index, method_index] = True
            mean_curves[panel_index, method_index] = (
                experiment["mean_results"][method_name]
            )

            for repetition_index, run_result in enumerate(
                experiment["all_results"]
            ):

                repetition_curves[
                    panel_index,
                    repetition_index,
                    method_index,
                ] = run_result[method_name]

        panel_completion_rounds = np.asarray(
            experiment["completion_rounds"],
            dtype=np.int32,
        )

        completion_rounds[
            panel_index,
            :panel_completion_rounds.size,
        ] = panel_completion_rounds

    np.savez_compressed(
        output_path,
        rounds=np.arange(NUM_ROUNDS + 1, dtype=np.int32),
        method_names=np.asarray(method_names, dtype=str),
        panel_labels=np.asarray(
            [experiment["config"]["panel"] for experiment in experiments],
            dtype=str,
        ),
        method_present=method_present,
        mean_curves=mean_curves,
        repetition_curves=repetition_curves,
        completion_rounds=completion_rounds,
        configs_json=np.asarray(
            json.dumps(
                [experiment["config"] for experiment in experiments]
            )
        ),
    )

    print(f"Saved calculated arrays to {output_path}")


def load_experiments(
    input_path=OUTPUT_DATA,
):

    saved = np.load(input_path, allow_pickle=False)
    method_names = [
        "Threshold" if name == "Battery threshold" else name
        for name in saved["method_names"].tolist()
    ]
    configs = json.loads(str(saved["configs_json"]))
    method_present = saved["method_present"]
    mean_curves = saved["mean_curves"]
    repetition_curves = saved["repetition_curves"]
    saved_completion_rounds = saved["completion_rounds"]

    experiments = []

    for panel_index, config in enumerate(configs):

        methods = [
            method_name
            for method_index, method_name in enumerate(method_names)
            if method_present[panel_index, method_index]
        ]

        mean_results = {
            method_name: mean_curves[
                panel_index,
                method_names.index(method_name),
            ]
            for method_name in methods
        }

        valid_completion_rounds = saved_completion_rounds[panel_index]
        valid_completion_rounds = valid_completion_rounds[
            valid_completion_rounds >= 0
        ].tolist()

        all_results = []
        for repetition_index in range(repetition_curves.shape[1]):

            run_result = {}
            for method_name in methods:

                curve = repetition_curves[
                    panel_index,
                    repetition_index,
                    method_names.index(method_name),
                ]

                if not np.all(np.isnan(curve)):
                    run_result[method_name] = curve

            if run_result:
                all_results.append(run_result)

        experiments.append({
            "config": config,
            "methods": methods,
            "mean_results": mean_results,
            "all_results": all_results,
            "completion_rounds": valid_completion_rounds,
        })

    print(f"Loaded calculated arrays from {input_path}")
    return experiments


# =========================================================
# PLOT PANEL
# =========================================================
def plot_panel(
    ax,
    experiment,
):

    config = (
        experiment[
            "config"
        ]
    )


    rounds = np.arange(

        NUM_ROUNDS
        +
        1
    )


    for method_name in (

        experiment[
            "methods"
        ]
    ):

        ax.plot(

            rounds,

            100.0
            *
            experiment[
                "mean_results"
            ][
                method_name
            ],

            label=
                DISPLAY_NAMES.get(method_name, method_name),

            linewidth=
                1.3,

            markersize=
                3.8,

            markeredgewidth=
                0.6,

            zorder=(

                7

                if method_name == "Linear Meta-Completion (LMC)"

                else 6

                if method_name == "Identity-Aware Protocol with Message Re-broadcasting (ID+R)"

                else 3
            ),

            **STYLES[
                method_name
            ],
        )


    completion_rounds = np.asarray(

        experiment[
            "completion_rounds"
        ],

        dtype=float,
    )


    completion_min = float(

        np.min(
            completion_rounds
        )
    )


    completion_max = float(

        np.max(
            completion_rounds
        )
    )


    if config[
        "dropout"
    ]:

        ax.axvline(

            x=
                config[
                    "failure_round"
                ],

            color=
                "#e377c2",

            linestyle=
                "--",

            linewidth=
                1.4,

            label=(

                "Permanent dropout "
                f"(round "
                f"{config['failure_round']})"
            ),

            zorder=
                2,
        )


        completion_label = (

            "Surviving-swarm "
            "completion range "
            f"("
            f"{completion_min:.0f}"
            f"–"
            f"{completion_max:.0f}"
            f")"
        )


        ylabel = (
            "Mean number of agents "
            "signaling Meta-Completion"
        )


    else:

        completion_label = (

            "True global completion range"
        )


        ylabel = (
            "Mean number of agents "
            "signaling Meta-Completion"
        )


    ax.axvspan(

        completion_min,

        completion_max,

        color=
            "gray",

        alpha=
            0.18,

        linewidth=
            0,

        label=
            completion_label,

        zorder=
            1,
    )


    ax.set_xlabel(
        "Round"
    )


    ax.set_ylabel(
        ylabel
    )


    ax.set_xlim(

        0,

        NUM_ROUNDS,
    )


    ax.set_ylim(

        -4,

        104,
    )


    ax.set_yticks(

        (
            0,
            20,
            40,
            60,
            80,
            100,
        )
    )


    ax.grid(

        True,

        alpha=
            0.30,

        linestyle=
            "--",

        linewidth=
            0.8,
    )


    ax.set_axisbelow(
        True
    )


    ax.text(

        -0.14,

        1.04,

        config[
            "panel"
        ],

        transform=
            ax.transAxes,

        fontsize=
            11,

        fontweight=
            "bold",

        ha=
            "left",

        va=
            "bottom",

        clip_on=
            False,
    )


    # -----------------------------------------------------
    # Heterogeneous-charging panel annotation
    # -----------------------------------------------------
    if config.get(
        "heterogeneous_charging",
        False,
    ):

        num_slow_agents = int(

            config[
                "num_slow_agents"
            ]
        )


        ax.text(

            0.98,

            0.06,

            (

                f"{100 - num_slow_agents} robots: "
                f"+{CHARGE_PER_ROUND:g}/round\n"

                f"{num_slow_agents} robots: "
                f"+{float(config['slow_charge_per_round']):g}/round"
            ),

            transform=
                ax.transAxes,

            fontsize=
                9.5,

            ha=
                "right",

            va=
                "bottom",
        )


    # A single shared legend is added after all three panels
    # have been drawn.


# =========================================================
# TRIAL-LEVEL PREMATURE-TRANSITION SUMMARY
# Uses the results produced in the same run.  No external
# .npz file is required for this second figure.
# =========================================================
def plot_premature_transition_counts(experiments):

    short_names = {
        "Threshold": "Threshold",
        "Centralised controller": "Centralised",
        "Fixed-membership centralised controller": "Centralised",
        "Full-state flooding": "Flooding",
        "Anonymous Protocol": "Anonymous",
        "Identity-Aware Protocol with Message Re-broadcasting (ID+R)": "ID+R",
        "Linear Meta-Completion (LMC)": "LMC",
    }

    trial_rows = []
    summary_rows = []

    for experiment in experiments:
        panel = experiment["config"]["panel"]
        num_agents = int(
            experiment["config"]["rows"]
            * experiment["config"]["columns"]
        )

        if len(experiment["all_results"]) != len(
            experiment["completion_rounds"]
        ):
            raise ValueError(
                f"Panel {panel}: run curves and completion rounds do not match."
            )

        panel_counts = {method: 0 for method in experiment["methods"]}

        for repetition_index, (run_result, ground_truth) in enumerate(
            zip(
                experiment["all_results"],
                experiment["completion_rounds"],
            ),
            start=1,
        ):
            ground_truth = int(ground_truth)

            for method in experiment["methods"]:
                curve = np.asarray(run_result[method], dtype=float)
                first_indices = np.flatnonzero(curve > 1e-12)
                first_transition = (
                    int(first_indices[0]) if first_indices.size else None
                )

                # Equality is not premature.  A run is counted only when
                # at least one robot changes state strictly before the
                # independently calculated global-completion round.
                premature = bool(
                    first_transition is not None
                    and first_transition < ground_truth
                )
                panel_counts[method] += int(premature)

                trial_rows.append(
                    {
                        "Panel": panel,
                        "Agents": num_agents,
                        "Trial": repetition_index,
                        "Method": method,
                        "Ground_truth_round": ground_truth,
                        "First_transition_round": (
                            "" if first_transition is None else first_transition
                        ),
                        "Premature": premature,
                    }
                )

        num_runs = len(experiment["all_results"])
        for method in experiment["methods"]:
            summary_rows.append(
                {
                    "Panel": panel,
                    "Agents": num_agents,
                    "Method": method,
                    "Premature_runs": panel_counts[method],
                    "Total_runs": num_runs,
                }
            )

    with open(PREMATURE_TRIAL_CSV, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(trial_rows[0]))
        writer.writeheader()
        writer.writerows(trial_rows)

    with open(PREMATURE_SUMMARY_CSV, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary_rows[0]))
        writer.writeheader()
        writer.writerows(summary_rows)

    fig, axes = plt.subplots(
        1,
        len(experiments),
        figsize=(18.4 / 2.54, 7.0 / 2.54),
        sharey=True,
    )
    axes = np.atleast_1d(axes)

    for panel_index, (ax, experiment) in enumerate(zip(axes, experiments)):
        panel = experiment["config"]["panel"]
        panel_rows = [row for row in summary_rows if row["Panel"] == panel]
        methods = [row["Method"] for row in panel_rows]
        counts = np.asarray(
            [row["Premature_runs"] for row in panel_rows],
            dtype=int,
        )
        totals = np.asarray(
            [row["Total_runs"] for row in panel_rows],
            dtype=int,
        )
        x = np.arange(len(methods))

        bars = ax.bar(
            x,
            counts,
            color=[STYLES[method]["color"] for method in methods],
            edgecolor="black",
            linewidth=0.8,
        )
        ax.bar_label(
            bars,
            labels=[f"{count}/{total}" for count, total in zip(counts, totals)],
            padding=2,
            fontsize=9.5,
        )
        ax.set_xticks(x)
        ax.set_xticklabels(
            [short_names.get(method, method) for method in methods],
            rotation=35,
            ha="right",
            fontsize=9.5,
        )
        ax.tick_params(axis="y", labelsize=9.5)
        max_runs = int(np.max(totals))
        ax.set_ylim(0, max_runs + 1)
        ax.set_yticks(np.arange(0, max_runs + 1, 2))
        ax.grid(axis="y", color="#D9D9D9", linewidth=0.5)
        ax.set_axisbelow(True)
        num_agents = int(
            experiment["config"]["rows"]
            * experiment["config"]["columns"]
        )
        panel_title = f"{panel}   $N={num_agents}$"
        if experiment["config"].get("heterogeneous_charging", False):
            panel_title += ", heterogeneous"

        ax.set_title(
            panel_title,
            loc="left",
            fontweight="bold",
            fontsize=10,
        )
        if panel_index == 0:
            ax.set_ylabel(
                "Runs with a premature transition",
                fontsize=10,
            )

    fig.subplots_adjust(
        left=0.08,
        right=0.99,
        bottom=0.29,
        top=0.90,
        wspace=0.25,
    )
    fig.savefig(
        PREMATURE_OUTPUT_PNG,
        dpi=600,
    )
    fig.savefig(
        PREMATURE_OUTPUT_PDF,
    )

    print(f"Saved {PREMATURE_TRIAL_CSV}")
    print(f"Saved {PREMATURE_SUMMARY_CSV}")
    print(f"Saved {PREMATURE_OUTPUT_PNG}")
    print(f"Saved {PREMATURE_OUTPUT_PDF}")

    for row in summary_rows:
        print(
            f"Panel {row['Panel']}, {short_names.get(row['Method'], row['Method']).replace(chr(10), ' ')}: "
            f"{row['Premature_runs']}/{row['Total_runs']} premature runs"
        )


# =========================================================
# MAIN
# =========================================================
def main():

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(
        "="
        *
        70
    )


    print(
        "INITIATING / META-COMPLETION CONFIGURATION"
    )


    print(

        f"Rounds = "
        f"{NUM_ROUNDS}"
    )


    print(

        f"Panels A-B default charging = "
        f"+{CHARGE_PER_ROUND:g}/round"
    )


    print(

        f"Panel C charging = "
        f"{100 - NUM_SLOW_AGENTS} robots at "
        f"+{CHARGE_PER_ROUND:g}/round, "
        f"{NUM_SLOW_AGENTS} robots at "
        f"+{SLOW_CHARGE_PER_ROUND:g}/round"
    )


    print(

        "All robots are stationary. "
        "Panel B uses a 10x100 grid; "
        "the other panels use 10x10 grids."
    )


    print(

        "Communication: "
        "up/down/left/right only."
    )


    print()


    print(
        "FLOODING"
    )


    print(

        "Julian-style "
        "full-table simple flooding."
    )


    print(

        "Each robot stores "
        "UID -> (state, timestamp)."
    )


    print(

        "Every active sender broadcasts "
        "its entire table to all "
        "orthogonal neighbours per round."
    )


    print(

        "Receiver keeps the newest "
        "timestamp for each UID."
    )


    print(

        "Flooding decision: "
        "all N known AND all N state=1."
    )


    print()


    print(
        "ID+R"
    )


    print(

        f"B_m = "
        f"{IDR_MIN_BUFFER}"
    )


    print(

        f"T_m = "
        f"{IDR_MEAN_TIMEOUT}"
    )


    print(

        f"tau = "
        f"{IDR_TAU}"
    )


    print(
        "="
        *
        70
    )


    # =====================================================
    # RUN
    # =====================================================
    if RUN_SIMULATION or not Path(OUTPUT_DATA).is_file():

        experiments = [

            run_experiment(
                config
            )

            for config
            in EXPERIMENTS
        ]

        save_experiments(
            experiments,
            OUTPUT_DATA,
        )

    else:

        experiments = load_experiments(
            OUTPUT_DATA
        )


    # =====================================================
    # PLOT SETTINGS
    # =====================================================
    plt.rcParams.update({

        "font.family":
            "sans-serif",

        "font.sans-serif": [

            "Arial",

            "Helvetica",

            "DejaVu Sans",
        ],

        "font.size":
            9.5,

        "axes.labelsize":
            10,

        "axes.titlesize":
            10,

        "xtick.labelsize":
            9.5,

        "ytick.labelsize":
            9.5,

        "legend.fontsize":
            9.5,

        "axes.linewidth":
            0.8,

        "xtick.major.width":
            0.8,

        "ytick.major.width":
            0.8,

        "pdf.fonttype":
            42,

        "ps.fonttype":
            42,
    })


    # =====================================================
    # FIGURE
    # =====================================================
    fig, axes = plt.subplots(

        nrows=
            1,

        ncols=
            3,

        figsize=
            (18.4 / 2.54, 8.8 / 2.54),

        sharex=
            True,

        sharey=
            True,
    )


    axes = np.asarray(axes).ravel()


    for (
        ax,
        experiment,
    ) in zip(

        axes,

        experiments,
    ):

        plot_panel(

            ax,

            experiment,
        )


    # =====================================================
    # SHARED LEGEND
    # =====================================================
    handles = []
    labels = []
    seen_labels = set()

    for ax in axes:

        panel_handles, panel_labels = (
            ax.get_legend_handles_labels()
        )

        for handle, label in zip(
            panel_handles,
            panel_labels,
        ):

            if label in seen_labels:
                continue

            handles.append(handle)
            labels.append(label)
            seen_labels.add(label)


    fig.legend(
        handles,
        labels,
        loc="lower center",
        bbox_to_anchor=(0.50, 0.015),
        ncol=7,
        frameon=False,
        fontsize=9.5,
        handlelength=1.6,
        handletextpad=0.4,
        columnspacing=0.85,
    )


    fig.subplots_adjust(

        left=
            0.055,

        right=
            0.985,

        bottom=
            0.27,

        top=
            0.94,

        wspace=
            0.28,
    )


    # =====================================================
    # SAVE
    # =====================================================
    fig.savefig(

        OUTPUT_PDF,

        format=
            "pdf",

        bbox_inches=
            "tight",
    )


    fig.savefig(

        OUTPUT_PNG,

        dpi=
            600,
    )


    print(

        f"Saved "
        f"{OUTPUT_PDF}"
    )


    print(

        f"Saved "
        f"{OUTPUT_PNG}"
    )


    # The same in-memory ten-run results now produce the second figure.
    # This avoids the earlier FileNotFoundError caused by a separate cell
    # trying to load /content/lmc_battery_simulation_results.npz.
    plot_premature_transition_counts(experiments)

    plt.show()


# =========================================================
# RUN
# =========================================================
if __name__ == "__main__":

    main()
