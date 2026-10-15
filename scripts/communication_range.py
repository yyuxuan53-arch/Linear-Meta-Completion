import numpy as np
import matplotlib.pyplot as plt

from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.lines import Line2D
from numba import njit, prange

# ============================================================
# 1. Plot settings
# ============================================================
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'DejaVu Sans'],
    'mathtext.fontset': 'dejavusans',

    'font.size': 9,
    'axes.labelsize': 10,
    'axes.titlesize': 10,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'legend.fontsize': 9,

    'lines.linewidth': 1.5,
    'lines.markersize': 6,

    'axes.grid': False,
    'axes.linewidth': 0.8,
    'xtick.direction': 'out',
    'ytick.direction': 'out',
})

# ============================================================
# 2. Simulation parameters
# ============================================================
TOTAL_AGENTS = 100
COMPLETED_AGENTS = 90
UNFINISHED_AGENTS = TOTAL_AGENTS - COMPLETED_AGENTS

# Fixed completed fraction.
R_COMPLETED = COMPLETED_AGENTS / TOTAL_AGENTS

# Abstract spatial arena, measured in simulation pixels.
SIM_WIDTH = 750.0
SIM_HEIGHT = 650.0

PHYSICAL_RADIUS = 4.0

# Abstract displacement per simulation round.
MOVE_SPEED = 1.0

# Communication ranges to compare.
COMM_RANGES = [100.0, 200.0, 300.0]

# Abstract simulation horizon.
TOTAL_ROUNDS = 200

# All agents begin with zero belief.
INITIAL_BELIEF = 0.0

BELIEF_THRESHOLD = 0.99
CONFIRMATION_ROUNDS = 10

# Parameter grid: 0.00, 0.01, ..., 1.00.
K_RESOLUTION = 101

# One spatial realisation per parameter map.
# Increase for a repeated-run analysis.
N_REPEATS = 10

# With multiple repetitions:
# red means at least one repetition contains a confirmed transition.
BASE_SEED = 20260901

# ============================================================
# 3. Parameter grid
# ============================================================
k1_values = np.linspace(
    0.0,
    1.0,
    K_RESOLUTION,
)

k2_values = np.linspace(
    0.0,
    1.0,
    K_RESOLUTION,
)

K1, K2 = np.meshgrid(
    k1_values,
    k2_values,
)

# The manuscript assumes k1 + k2 < 1.
# The diagonal is drawn as a boundary but is not classified.
valid = (
    (K1 > 0.0)
    & (K2 > 0.0)
    & (K1 + K2 < 1.0 - 1e-12)
)

k1_points = K1[valid].copy()
k2_points = K2[valid].copy()

n_parameter_points = len(k1_points)

# ============================================================
# 4. Generate motion and spatial pairings
#
# Each round:
#   1. Every agent moves once.
#   2. Agents are randomly ordered.
#   3. Each unpaired agent randomly selects one available
#      neighbour inside the communication range.
#   4. Each agent participates in at most one pair.
#
# This is a random local pairwise-interaction model.
# It is not mapped to Kilobot physical time.
# ============================================================
@njit
def build_pair_schedule(
    comm_range,
    n_agents,
    total_rounds,
    width,
    height,
    physical_radius,
    move_speed,
    seed,
):
    np.random.seed(seed)

    # --------------------------------------------------------
    # Initial positions and velocities
    # --------------------------------------------------------
    x = np.empty(n_agents)
    y = np.empty(n_agents)

    vx = np.empty(n_agents)
    vy = np.empty(n_agents)

    for i in range(n_agents):
        x[i] = np.random.uniform(
            physical_radius,
            width - physical_radius,
        )

        y[i] = np.random.uniform(
            physical_radius,
            height - physical_radius,
        )

        angle = np.random.uniform(
            0.0,
            2.0 * np.pi,
        )

        vx[i] = move_speed * np.cos(angle)
        vy[i] = move_speed * np.sin(angle)

    # At most N/2 disjoint pairs can be formed per round.
    max_pairs = n_agents // 2

    pairs = np.full(
        (total_rounds, max_pairs, 2),
        -1,
        dtype=np.int16,
    )

    pair_counts = np.zeros(
        total_rounds,
        dtype=np.int16,
    )

    indices = np.arange(n_agents)

    updated = np.zeros(
        n_agents,
        dtype=np.bool_,
    )

    neighbours = np.empty(
        n_agents,
        dtype=np.int64,
    )

    range_squared = comm_range * comm_range

    # Keep initial motion identical across communication ranges
    # while separating the pairing random-number stream.
    np.random.seed(seed + 100_000)

    # --------------------------------------------------------
    # Generate one motion/pairing schedule
    # --------------------------------------------------------
    for round_index in range(total_rounds):

        # ----------------------------------------------------
        # Move every agent once.
        # ----------------------------------------------------
        for i in range(n_agents):
            x[i] += vx[i]
            y[i] += vy[i]

            # Reflect at left boundary.
            if x[i] < physical_radius:
                excess = physical_radius - x[i]
                x[i] = physical_radius + excess
                vx[i] *= -1.0

            # Reflect at right boundary.
            if x[i] > width - physical_radius:
                excess = (
                    x[i]
                    - (width - physical_radius)
                )

                x[i] = (
                    width
                    - physical_radius
                    - excess
                )

                vx[i] *= -1.0

            # Reflect at bottom boundary.
            if y[i] < physical_radius:
                excess = physical_radius - y[i]
                y[i] = physical_radius + excess
                vy[i] *= -1.0

            # Reflect at top boundary.
            if y[i] > height - physical_radius:
                excess = (
                    y[i]
                    - (height - physical_radius)
                )

                y[i] = (
                    height
                    - physical_radius
                    - excess
                )

                vy[i] *= -1.0

        # ----------------------------------------------------
        # Randomly form disjoint communication pairs.
        # ----------------------------------------------------
        for i in range(n_agents):
            indices[i] = i
            updated[i] = False

        np.random.shuffle(indices)

        pair_count = 0

        for position in range(n_agents):
            receiver = indices[position]

            if updated[receiver]:
                continue

            neighbour_count = 0

            # Find currently unpaired neighbours in range.
            for candidate in range(n_agents):
                if candidate == receiver:
                    continue

                if updated[candidate]:
                    continue

                dx = x[receiver] - x[candidate]
                dy = y[receiver] - y[candidate]

                distance_squared = dx * dx + dy * dy

                if distance_squared <= range_squared:
                    neighbours[neighbour_count] = candidate
                    neighbour_count += 1

            if neighbour_count > 0:
                selected_position = np.random.randint(
                    0,
                    neighbour_count,
                )

                neighbour = neighbours[
                    selected_position
                ]

                pairs[
                    round_index,
                    pair_count,
                    0,
                ] = receiver

                pairs[
                    round_index,
                    pair_count,
                    1,
                ] = neighbour

                updated[receiver] = True
                updated[neighbour] = True

                pair_count += 1

        pair_counts[round_index] = pair_count

    return pairs, pair_counts


# ============================================================
# 5. Evaluate the complete k1-k2 grid
#
# Completed agents:
#
# P_i(t+1)
#   = k1*P_i(t)
#   + k2*P_j(t)
#   + (1-k1-k2)
#
# Unfinished agents always remain at zero.
#
# Both agents use pre-interaction beliefs.
#
# For a full-completion run, success requires every robot to confirm by T.
# For a partial-completion run, an event means any robot confirms by T.
# ============================================================
@njit(parallel=True)
def evaluate_parameter_grid(
    k1_array,
    k2_array,
    pairs,
    pair_counts,
    n_agents,
    completed_agents,
    initial_belief,
    threshold,
    confirmation_rounds,
    require_all,
):
    n_points = len(k1_array)
    n_rounds = len(pair_counts)
    decisions = np.zeros(n_points, dtype=np.bool_)

    for parameter_index in prange(n_points):

        k1 = k1_array[parameter_index]
        k2 = k2_array[parameter_index]

        source_weight = (
            1.0 - k1 - k2
        )

        beliefs = np.full(
            n_agents,
            initial_belief,
        )

        consecutive = np.zeros(
            n_agents,
            dtype=np.int16,
        )

        confirmed = np.zeros(
            n_agents,
            dtype=np.bool_,
        )

        # Explicitly keep unfinished agents at zero.
        for i in range(
            completed_agents,
            n_agents,
        ):
            beliefs[i] = 0.0

        for round_index in range(n_rounds):

            number_of_pairs = pair_counts[
                round_index
            ]

            for pair_index in range(number_of_pairs):

                i = pairs[
                    round_index,
                    pair_index,
                    0,
                ]

                j = pairs[
                    round_index,
                    pair_index,
                    1,
                ]

                # Store pre-interaction beliefs.
                old_i = beliefs[i]
                old_j = beliefs[j]

                # Completed receiver i.
                if i < completed_agents:
                    new_i = (
                        k1 * old_i
                        + k2 * old_j
                        + source_weight
                    )
                else:
                    new_i = 0.0

                # Completed receiver j.
                if j < completed_agents:
                    new_j = (
                        k1 * old_j
                        + k2 * old_i
                        + source_weight
                    )
                else:
                    new_j = 0.0

                beliefs[i] = new_i
                beliefs[j] = new_j

            # Apply the confirmation rule once per simulation round.
            # A below-threshold round resets that robot's counter.
            for i in range(n_agents):
                if beliefs[i] >= threshold:
                    consecutive[i] += 1
                else:
                    consecutive[i] = 0

                if consecutive[i] >= confirmation_rounds:
                    confirmed[i] = True

            if require_all:
                all_confirmed = True
                for i in range(n_agents):
                    if not confirmed[i]:
                        all_confirmed = False
                        break
                if all_confirmed:
                    decisions[parameter_index] = True
                    break
            else:
                any_confirmed = False
                for i in range(n_agents):
                    if confirmed[i]:
                        any_confirmed = True
                        break
                if any_confirmed:
                    decisions[parameter_index] = True
                    break

    return decisions


# ============================================================
# 6. Run all communication ranges
# ============================================================
print("=" * 65)
print("SPATIAL COMMUNICATION-RANGE SIMULATION")
print("=" * 65)

print(
    f"Agents: {TOTAL_AGENTS}"
)

print(
    f"Completed agents: {COMPLETED_AGENTS}"
)

print(
    f"Unfinished agents: {UNFINISHED_AGENTS}"
)

print(
    f"Completed fraction: {R_COMPLETED:.2f}"
)

print(
    f"Simulation horizon: {TOTAL_ROUNDS} rounds"
)

print(
    "Each round contains one movement step, one spatial "
    "pairing step, one belief update, and one threshold check."
)

print(
    f"Valid parameter points: {n_parameter_points}"
)

print(
    f"Repetitions per communication range: {N_REPEATS}"
)

print(
    f"Confirmation rule: {CONFIRMATION_ROUNDS} consecutive rounds"
)

print(
    "The first call also compiles the Numba functions."
)

all_optimistic_maps = []

for range_index, comm_range in enumerate(COMM_RANGES):

    full_success_counts = np.zeros(
        n_parameter_points,
        dtype=np.int32,
    )
    premature_counts = np.zeros(
        n_parameter_points,
        dtype=np.int32,
    )

    print(
        f"\nCommunication range: "
        f"{comm_range:g} px"
    )

    for repeat in range(N_REPEATS):

        # Repetitions differ, but initial trajectories are
        # matched across communication ranges.
        run_seed = (
            BASE_SEED
            + repeat * 1_000_000
        )

        print(
            f"  Repetition {repeat + 1}/"
            f"{N_REPEATS}: generating schedule..."
        )

        pairs, pair_counts = build_pair_schedule(
            comm_range,
            TOTAL_AGENTS,
            TOTAL_ROUNDS,
            SIM_WIDTH,
            SIM_HEIGHT,
            PHYSICAL_RADIUS,
            MOVE_SPEED,
            run_seed,
        )

        print("  Evaluating full-completion condition...")
        full_success = evaluate_parameter_grid(
            k1_points,
            k2_points,
            pairs,
            pair_counts,
            TOTAL_AGENTS,
            TOTAL_AGENTS,
            INITIAL_BELIEF,
            BELIEF_THRESHOLD,
            CONFIRMATION_ROUNDS,
            True,
        )

        print("  Evaluating partial-completion condition...")
        premature_event = evaluate_parameter_grid(
            k1_points,
            k2_points,
            pairs,
            pair_counts,
            TOTAL_AGENTS,
            COMPLETED_AGENTS,
            INITIAL_BELIEF,
            BELIEF_THRESHOLD,
            CONFIRMATION_ROUNDS,
            False,
        )

        full_success_counts += full_success
        premature_counts += premature_event

        del pairs
        del pair_counts
        del full_success
        del premature_event

    # Conservative finite-run classification: every full-completion run
    # must succeed and no partial-completion run may confirm prematurely.
    optimistic_map = (
        (full_success_counts == N_REPEATS)
        & (premature_counts == 0)
    )
    all_optimistic_maps.append(optimistic_map)

    print(
        f"  Optimistic parameter points: "
        f"{np.count_nonzero(optimistic_map)}"
    )

# ============================================================
# 7. Plot three heatmaps
# ============================================================
GREY = '#D9D9D9'
BLUE = '#2878B5'

cmap = ListedColormap([
    GREY,
    BLUE,
])

# Outside the admissible triangle remains white.
cmap.set_bad('white')

norm = BoundaryNorm(
    [-0.5, 0.5, 1.5],
    ncolors=2,
)

fig, axes = plt.subplots(
    1,
    3,
    figsize=(18.4 / 2.54, 7.8 / 2.54),
)

fig.subplots_adjust(
    left=0.07,
    right=0.99,
    bottom=0.31,
    top=0.86,
    wspace=0.34,
)

dx = k1_values[1] - k1_values[0]
dy = k2_values[1] - k2_values[0]

for panel_index, (
    ax,
    comm_range,
    optimistic_map,
) in enumerate(
    zip(
        axes,
        COMM_RANGES,
        all_optimistic_maps,
    )
):
    heatmap = np.full(
        K1.shape,
        np.nan,
    )

    heatmap[valid] = optimistic_map.astype(float)

    image = ax.imshow(
        np.ma.masked_invalid(heatmap),
        origin='lower',
        extent=[
            k1_values[0] - dx / 2,
            k1_values[-1] + dx / 2,
            k2_values[0] - dy / 2,
            k2_values[-1] + dy / 2,
        ],
        cmap=cmap,
        norm=norm,
        interpolation='nearest',
        aspect='equal',
        zorder=1,
    )

    # Clip the cell edges to the exact triangular domain.
    triangle = plt.Polygon(
        [
            [0.0, 0.0],
            [1.0, 0.0],
            [0.0, 1.0],
        ],
        closed=True,
        transform=ax.transData,
    )

    image.set_clip_path(triangle)

    # Parameter-domain boundary.
    ax.plot(
        [0.0, 1.0],
        [1.0, 0.0],
        color='black',
        linewidth=0.9,
        zorder=3,
    )

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_aspect(
        'equal',
        adjustable='box',
    )

    ticks = np.linspace(0, 1, 6)

    ax.set_xticks(ticks)
    ax.set_yticks(ticks)

    ax.set_xlabel(r'$k_1$')
    ax.set_ylabel(r'$k_2$')

    ax.set_title(
        f'Range = {comm_range:g} px',
        pad=6,
    )

    ax.grid(False, which='both')

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    # Panel labels A, B, C.
    ax.text(
        -0.16,
        1.07,
        chr(ord('A') + panel_index),
        transform=ax.transAxes,
        fontsize=11,
        fontweight='bold',
        ha='left',
        va='bottom',
        clip_on=False,
    )

# ============================================================
# 8. Shared legend
# ============================================================
legend_handles = [
    Line2D(
        [],
        [],
        marker='s',
        linestyle='none',
        markerfacecolor=BLUE,
        markeredgecolor='none',
        markersize=7,
        label='Admissible parameter region',
    ),
    Line2D(
        [],
        [],
        marker='s',
        linestyle='none',
        markerfacecolor=GREY,
        markeredgecolor='none',
        markersize=7,
        label='Outside region',
    ),
]

fig.legend(
    handles=legend_handles,
    loc='lower center',
    bbox_to_anchor=(0.5, 0.035),
    ncol=2,
    frameon=False,
    fontsize=9,
    columnspacing=1.8,
    handletextpad=0.5,
)

# No overall title and no file saving.
plt.show()

# ============================================================
# 9. Final summary
# ============================================================
print("\n" + "=" * 65)
print("FINAL SUMMARY")
print("=" * 65)

print(
    f"Simulation horizon: {TOTAL_ROUNDS} rounds"
)

print(
    f"Initial belief: {INITIAL_BELIEF}"
)

print(
    f"Belief threshold: {BELIEF_THRESHOLD}"
)

print(
    f"Completed fraction: {R_COMPLETED:.2f}"
)

print(
    f"Confirmation rounds: {CONFIRMATION_ROUNDS}"
)

for comm_range, optimistic_map in zip(
    COMM_RANGES,
    all_optimistic_maps,
):
    print(
        f"Range {comm_range:g} px: "
        f"optimistic={np.count_nonzero(optimistic_map)}, "
        f"outside={np.count_nonzero(~optimistic_map)}"
    )

