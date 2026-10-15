import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt

from matplotlib.colors import to_rgba
from matplotlib.lines import Line2D
from matplotlib.ticker import MaxNLocator
from scipy.stats import beta as beta_dist


# ============================================================
# Settings
# ============================================================
N = 100
T = 200
THETA = 0.99
TAU = 0.01
RUNS_MAP = 10
RUNS_BAR = 1000
SEED = 20260921
R_VALUES = (0.90, 0.99)

BLUE = "#2878B5"       # theory and simulation
BLACK = "#111111"      # theory only
YELLOW = "#F2D93B"     # simulation only
GREY = "#D9D9D9"       # neither
RED = "#D62728"

mpl.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "mathtext.fontset": "dejavusans",
    "font.size": 9,
    "axes.titlesize": 10,
    "axes.labelsize": 10,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 9,
    "axes.linewidth": 0.8,
})


def parameter_grid():
    values = np.linspace(0.0, 1.0, 101)
    k1_grid, k2_grid = np.meshgrid(values, values)
    valid = (k1_grid > 0) & (k2_grid > 0) & (k1_grid + k2_grid < 1)
    return k1_grid, k2_grid, valid


K1_GRID, K2_GRID, VALID = parameter_grid()
K1 = K1_GRID[VALID]
K2 = K2_GRID[VALID]
N_POINTS = K1.size
POINT_INDEX = np.arange(N_POINTS)[:, None]
TRIAL_INDEX = np.arange(RUNS_MAP)[None, :]


def simulate_condition(completed_count, confirmation_rounds, seed):
    """Return whether every valid parameter pair produces a threshold event."""
    rng = np.random.default_rng(seed)
    beliefs = np.zeros((N_POINTS, RUNS_MAP, N), dtype=np.float32)
    states = np.zeros(N, dtype=np.float32)
    states[:completed_count] = 1.0

    if confirmation_rounds == 1:
        confirmed = np.zeros((N_POINTS, RUNS_MAP, N), dtype=bool)
        consecutive = None
    else:
        confirmed = np.zeros((N_POINTS, RUNS_MAP, N), dtype=bool)
        consecutive = np.zeros((N_POINTS, RUNS_MAP, N), dtype=np.uint8)

    for _ in range(T):
        for i in range(N):
            partners = rng.integers(0, N - 1, size=(N_POINTS, RUNS_MAP))
            partners += partners >= i
            if states[i] == 0:
                beliefs[:, :, i] = 0.0
            else:
                neighbor = beliefs[POINT_INDEX, TRIAL_INDEX, partners]
                beliefs[:, :, i] = (
                    K1[:, None] * beliefs[:, :, i]
                    + K2[:, None] * neighbor
                    + (1.0 - K1 - K2)[:, None]
                )

            above = beliefs[:, :, i] >= THETA
            if confirmation_rounds == 1:
                confirmed[:, :, i] |= above
            else:
                consecutive[:, :, i] = np.where(
                    above,
                    np.minimum(consecutive[:, :, i] + 1, confirmation_rounds),
                    0,
                )
                confirmed[:, :, i] |= (
                    consecutive[:, :, i] >= confirmation_rounds
                )

    result = np.zeros(VALID.shape, dtype=bool)
    if completed_count == N:
        # All robots must confirm in every replicate.
        result[VALID] = confirmed.all(axis=2).all(axis=1)
    else:
        # A confirmation by any robot in any replicate is premature.
        result[VALID] = confirmed.any(axis=2).any(axis=1)
    return result


def analytically_predicted_admissible_region(r):
    """Return the analytically predicted admissible region for one completed fraction."""
    theory_full_values = 1.0 - (K1 + K2) ** T >= THETA

    completed_count = int(round(r * N))
    rho = (completed_count - 1) / (N - 1)
    a = K1 + rho * K2
    b = 1.0 - K1 - K2
    c = K1**2 + rho * K2**2
    d = rho * (1.0 - rho) * K2**2
    mu = np.zeros_like(K1)
    variance = np.zeros_like(K1)
    partial_hit = np.zeros_like(K1, dtype=bool)

    for _ in range(T):
        variance_next = c * variance + d * mu**2
        mu_next = a * mu + b
        variance, mu = variance_next, mu_next

        quantile = np.empty_like(mu)
        deterministic = variance <= np.finfo(float).eps
        quantile[deterministic] = mu[deterministic]
        stochastic = ~deterministic
        if np.any(stochastic):
            mu_s = mu[stochastic]
            variance_s = variance[stochastic]
            nu = mu_s * (1.0 - mu_s) / variance_s - 1.0
            quantile[stochastic] = beta_dist.ppf(
                1.0 - TAU,
                mu_s * nu,
                (1.0 - mu_s) * nu,
            )
        partial_hit |= quantile >= THETA

    region = np.zeros(VALID.shape, dtype=bool)
    region[VALID] = theory_full_values & ~partial_hit
    return region


def simulation_derived_admissible_region(r, confirmation_rounds=1):
    """Return the simulation-derived admissible region."""
    completed_count = int(round(r * N))
    seed_base = SEED + int(round(1000 * r)) + 100 * confirmation_rounds
    full_success = simulate_condition(
        N, confirmation_rounds, seed_base
    )
    partial_hit = simulate_condition(
        completed_count, confirmation_rounds, seed_base + 1
    )
    return full_success & ~partial_hit


def premature_counts(k1=0.40, k2=0.53):
    """Retained current panel-F result."""
    horizons = np.asarray([200, 600, 2000])
    counts = np.zeros((2, len(horizons)), dtype=int)
    rng = np.random.default_rng(SEED + 100)
    beliefs = np.zeros((RUNS_BAR, N), dtype=np.float64)
    consecutive = np.zeros((RUNS_BAR, N), dtype=np.uint8)
    single_hit = np.zeros(RUNS_BAR, dtype=bool)
    confirmed_hit = np.zeros(RUNS_BAR, dtype=bool)
    run_index = np.arange(RUNS_BAR)

    for round_number in range(1, int(horizons[-1]) + 1):
        for i in range(N):
            partners = rng.integers(0, N - 1, size=RUNS_BAR)
            partners += partners >= i
            if i == N - 1:
                beliefs[:, i] = 0.0
            else:
                beliefs[:, i] = (
                    k1 * beliefs[:, i]
                    + k2 * beliefs[run_index, partners]
                    + 1.0 - k1 - k2
                )
            above = beliefs[:, i] >= THETA
            single_hit |= above
            consecutive[:, i] = np.where(
                above, np.minimum(consecutive[:, i] + 1, 10), 0
            )
            confirmed_hit |= consecutive[:, i] >= 10

        if round_number in horizons:
            index = int(np.where(horizons == round_number)[0][0])
            counts[0, index] = single_hit.sum()
            counts[1, index] = confirmed_hit.sum()
    return horizons, counts


def draw_mask(ax, mask, color, zorder):
    rgba = np.zeros((*VALID.shape, 4), dtype=float)
    rgba[VALID & mask] = to_rgba(color)
    ax.imshow(
        rgba,
        origin="lower",
        extent=[-0.005, 1.005, -0.005, 1.005],
        interpolation="nearest",
        aspect="equal",
        zorder=zorder,
    )


def style_parameter_axis(ax, title):
    boundary = np.linspace(0, 1, 200)
    ax.plot(boundary, 1 - boundary, color="black", linewidth=0.9, zorder=8)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel(r"$k_1$")
    ax.set_ylabel(r"$k_2$")
    ax.set_title(title, pad=6)
    ax.spines[["top", "right"]].set_visible(False)


def square_legend(ax, entries, ncol=2):
    handles = [
        Line2D(
            [], [], marker="s", linestyle="none", markersize=7,
            markerfacecolor=color, markeredgecolor="none", label=label
        )
        for color, label in entries
    ]
    ax.legend(
        handles=handles,
        frameon=False,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.18),
        ncol=ncol,
        columnspacing=1.0,
        handletextpad=0.4,
    )


print("Calculating single-crossing admissible parameter regions...")
analytical_regions = {
    r: analytically_predicted_admissible_region(r) for r in R_VALUES
}
simulation_regions = {
    r: simulation_derived_admissible_region(r, confirmation_rounds=1)
    for r in R_VALUES
}

print("Calculating the 10-round-confirmation admissible parameter region...")
confirmation_region = simulation_derived_admissible_region(
    0.99, confirmation_rounds=10
)

print("Calculating retained horizon comparison...")
horizons, counts = premature_counts()


# ============================================================
# Four-panel final figure at full two-column page width
# ============================================================
fig, axes = plt.subplots(2, 2, figsize=(18.4 / 2.54, 17.2 / 2.54))
fig.subplots_adjust(
    left=0.09, right=0.985, bottom=0.095, top=0.96,
    wspace=0.34, hspace=0.78
)

for ax, r in zip(axes[0], R_VALUES):
    theory = analytical_regions[r]
    simulation = simulation_regions[r]
    both = theory & simulation
    theory_only = theory & ~simulation
    simulation_only = ~theory & simulation
    neither = ~theory & ~simulation

    draw_mask(ax, neither, GREY, 1)
    draw_mask(ax, both, BLUE, 2)
    draw_mask(ax, theory_only, BLACK, 3)
    draw_mask(ax, simulation_only, YELLOW, 4)
    style_parameter_axis(
        ax,
        rf"Admissible-region overlap" + "\n" + rf"($r={r:g}$)",
    )
    square_legend(
        ax,
        [
            (BLUE, "Theory and simulation"),
            (BLACK, "Theory only"),
            (YELLOW, "Simulation only"),
            (GREY, "Neither"),
        ],
        ncol=2,
    )


ax_c = axes[1, 0]
draw_mask(ax_c, ~confirmation_region, GREY, 1)
draw_mask(ax_c, confirmation_region, BLUE, 2)
style_parameter_axis(
    ax_c,
    "Simulation-derived admissible parameter region\n"
    r"(10-round confirmation, $r=0.99$)",
)
square_legend(
    ax_c,
    [
        (BLUE, "Admissible parameter region"),
        (GREY, "Outside region"),
    ],
    ncol=1,
)


ax_d = axes[1, 1]
positions = np.arange(len(horizons))
width = 0.36
bars_single = ax_d.bar(
    positions - width / 2,
    counts[0],
    width,
    color=RED,
    label="Single crossing",
)
bars_confirmed = ax_d.bar(
    positions + width / 2,
    counts[1],
    width,
    color=BLUE,
    label="10-round confirmation",
)
ax_d.set_xticks(positions, horizons)
ax_d.set_xlabel("Observation horizon, $T$")
ax_d.set_ylabel("Runs with a premature transition\n(out of 1000)")
ax_d.set_title(
    "Premature-transition counts\n"
    r"($N=100, m=99, k_1=0.40, k_2=0.53$)",
    pad=6,
)
ax_d.set_ylim(0, 120)
ax_d.yaxis.set_major_locator(MaxNLocator(nbins=6, integer=True))
ax_d.legend(frameon=False, loc="upper left")
ax_d.spines[["top", "right"]].set_visible(False)
ax_d.bar_label(bars_single, padding=2, fontsize=9)
ax_d.bar_label(bars_confirmed, padding=2, fontsize=9)


for ax, letter in zip(axes.flat, "ABCD"):
    ax.text(
        -0.14, 1.16, letter, transform=ax.transAxes,
        fontsize=11, fontweight="bold", ha="right", va="bottom",
        clip_on=False,
    )

plt.show()

