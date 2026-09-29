# Complete code-cell export of science_robotics.ipynb.
# Colab-only line magics are commented; run the notebook for those behaviors.

# %% [notebook cell 1]
from pathlib import Path
import base64
import html

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from PIL import Image
from google.colab import files
from IPython.display import display, HTML

# ====================== USER SETTINGS ======================

N = 100

T_COMPLETE = 21
T_FIRST_BLUE = 89
T_ALL_BLUE = 125

# Enter the verified control observation duration in seconds.
# None produces a clearly marked draft placeholder.
CONTROL_DURATION_S = 240

# Optional: actual timestamps of the displayed screenshots.
# Do not use event times unless the screenshots are those exact frames.
FRAME_TIMES_S = {
    "running": None,
    "finished": None,
    "metacompletion": None,
    "control": None,
}

# Optional manual identification of the unfinished agent.
# Coordinates must be measured on the original control image.
# Example format: (x_pixel, y_pixel). No position is assumed.
UNFINISHED_XY = None

FIG_WIDTH_CM = 18.4
FIG_HEIGHT_CM = 20.0
PREVIEW_WIDTH_PX = 1400
PNG_DPI = 600

IMAGE_FILES = {
    "running": "kilobotrunning.png",
    "finished": "kilobotfinished.png",
    "metacompletion": "kilobotmetacompletion.png",
    "control": "dancing_LMC_1unfinished.png",
}

OUTPUT_DIR = Path("/content/figure1_output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ====================== INPUT VALIDATION ======================

if not 0 <= T_COMPLETE <= T_FIRST_BLUE <= T_ALL_BLUE:
    raise ValueError("Check the normal-run event times.")

if CONTROL_DURATION_S is not None and CONTROL_DURATION_S <= 0:
    raise ValueError("The control duration must be positive.")

missing = [
    name for name in IMAGE_FILES.values()
    if not Path("/content", name).exists()
]

if missing:
    print("Upload these images:")
    print("\n".join(missing))
    uploaded = files.upload()

    for name, data in uploaded.items():
        Path("/content", Path(name).name).write_bytes(data)

missing = [
    name for name in IMAGE_FILES.values()
    if not Path("/content", name).exists()
]
if missing:
    raise FileNotFoundError("Missing images: " + ", ".join(missing))

images = {
    key: Image.open(Path("/content", name)).convert("RGB")
    for key, name in IMAGE_FILES.items()
}

# ====================== STYLE ======================

mpl.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": [
        "Arial", "Helvetica", "Liberation Sans", "DejaVu Sans"
    ],
    "font.size": 8,
    "axes.labelsize": 8,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "axes.linewidth": 0.7,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "svg.fonttype": "none",
    "savefig.facecolor": "white",
})

GREEN = "#17865B"
BLUE = "#1764BA"
DARK = "#252525"

fig = plt.figure(
    figsize=(FIG_WIDTH_CM / 2.54, FIG_HEIGHT_CM / 2.54),
    facecolor="white",
)

# Fixed positions preserve publication dimensions.
# Photos are shown whole, with their original aspect ratios.
PHOTO_WIDTH = 0.45
PHOTO_HEIGHT = 0.263
LEFT_X = 0.035
RIGHT_X = 0.515
TOP_Y = 0.685
BOTTOM_Y = 0.350

panels = [
    (
        "running", "A",
        "Task in progress",
        "Normal run | Yellow LED",
        [LEFT_X, TOP_Y, PHOTO_WIDTH, PHOTO_HEIGHT],
    ),
    (
        "finished", "B",
        "All robots locally complete",
        "Normal run | Green LED",
        [RIGHT_X, TOP_Y, PHOTO_WIDTH, PHOTO_HEIGHT],
    ),
    (
        "metacompletion", "C",
        "All robots detect the global completion",
        "Normal run | Blue LED",
        [LEFT_X, BOTTOM_Y, PHOTO_WIDTH, PHOTO_HEIGHT],
    ),
    (
        "control", "D",
        "One agent remains unfinished",
        "Control run | No blue signal observed",
        [RIGHT_X, BOTTOM_Y, PHOTO_WIDTH, PHOTO_HEIGHT],
    ),
]

photo_axes = {}

for key, letter, title, subtitle, position in panels:
    ax = fig.add_axes(position)
    photo_axes[key] = ax

    # No colour changes, sharpening, or generative processing.
    # "none" preserves native image sampling in the PDF backend.
    ax.imshow(images[key], interpolation="none")
    ax.set_axis_off()

    ax.text(
        0.0, 1.115, letter,
        transform=ax.transAxes,
        fontsize=10,
        fontweight="bold",
        ha="left",
        va="bottom",
        clip_on=False,
    )
    ax.text(
        0.065, 1.115, title,
        transform=ax.transAxes,
        fontsize=8.5,
        fontweight="bold",
        ha="left",
        va="bottom",
        clip_on=False,
    )
    ax.text(
        0.0, 1.015, subtitle,
        transform=ax.transAxes,
        fontsize=8,
        ha="left",
        va="bottom",
        clip_on=False,
    )

    timestamp = FRAME_TIMES_S[key]
    if timestamp is not None:
        ax.text(
            0.975, 0.97,
            f"{timestamp:g} s",
            transform=ax.transAxes,
            ha="right",
            va="top",
            color="white",
            fontsize=8,
            bbox={
                "facecolor": "black",
                "alpha": 0.65,
                "edgecolor": "none",
                "pad": 2,
            },
        )

# Optional annotation based only on user-confirmed coordinates.
if UNFINISHED_XY is not None:
    x, y = UNFINISHED_XY
    img = images["control"]

    if not (0 <= x < img.width and 0 <= y < img.height):
        raise ValueError("UNFINISHED_XY is outside the control image.")

    ax = photo_axes["control"]
    dx = -0.17 * img.width if x > img.width / 2 else 0.17 * img.width
    dy = -0.13 * img.height if y > img.height / 2 else 0.13 * img.height

    ax.annotate(
        "Unfinished",
        xy=(x, y),
        xytext=(x + dx, y + dy),
        color="white",
        fontsize=8,
        ha="center",
        va="center",
        bbox={
            "facecolor": "black",
            "alpha": 0.65,
            "edgecolor": "none",
            "pad": 2,
        },
        arrowprops={
            "arrowstyle": "->",
            "color": "white",
            "linewidth": 1.0,
        },
    )

# Control observation window, kept separate from screenshot time.
if CONTROL_DURATION_S is None:
    control_note = "Observation duration: 4 minutes"
else:
    control_note = f"Observation window: {CONTROL_DURATION_S:g} s"

photo_axes["control"].text(
    0.0, -0.055,
    control_note,
    transform=photo_axes["control"].transAxes,
    fontsize=8,
    ha="left",
    va="top",
    clip_on=False,
)

# ====================== PANEL E: EVENT TIMELINE ======================

ax = fig.add_axes([0.09, 0.065, 0.86, 0.205])

ax.text(
    -0.065, 1.075, "E",
    transform=ax.transAxes,
    fontsize=10,
    fontweight="bold",
    ha="left",
    va="bottom",
)
ax.text(
    0.0, 1.075,
    "Normal run: manually annotated completion and detection times",
    transform=ax.transAxes,
    fontsize=8.5,
    fontweight="bold",
    ha="left",
    va="bottom",
)

ax.set_xlim(0, T_ALL_BLUE + 15)
ax.set_ylim(-1.18, 1.0)
ax.set_yticks([])
ax.spines[["left", "right", "top"]].set_visible(False)
ax.set_xlabel("Time from the defined run origin (s)", labelpad=5)
ax.set_xticks(np.arange(0, T_ALL_BLUE + 16, 20))
ax.tick_params(axis="x", length=3, width=0.7)

# Event timeline only: no interpolated count or proportion curve.
ax.hlines(
    0.12, 0, T_ALL_BLUE,
    color="#B8B8B8", linewidth=1.1,
)

events = [
    (T_COMPLETE, GREEN, "s", "All locally\ncomplete"),
    (T_FIRST_BLUE, BLUE, "o", "First blue\nsignal"),
    (T_ALL_BLUE, BLUE, "D", "All blue"),
]

for t, color, marker, label in events:
    ax.scatter(
        t, 0.12,
        s=30,
        marker=marker,
        color=color,
        zorder=5,
    )
    ax.vlines(t, 0.12, 0.40, color=color, linewidth=0.8)
    ax.text(
        t, 0.49,
        f"{label}\n{t:g} s",
        ha="center",
        va="bottom",
        fontsize=8,
        linespacing=1.15,
    )

# Independently determined all-task completion reference.
ax.axvline(
    T_COMPLETE,
    color=GREEN,
    linewidth=0.9,
    linestyle=(0, (3, 3)),
    zorder=1,
)

def add_delay(start, end, y, text):
    ax.annotate(
        "",
        xy=(end, y),
        xytext=(start, y),
        arrowprops={
            "arrowstyle": "<->",
            "color": DARK,
            "linewidth": 0.8,
            "shrinkA": 0,
            "shrinkB": 0,
        },
    )
    ax.text(
        (start + end) / 2,
        y + 0.085,
        text,
        ha="center",
        va="bottom",
        fontsize=8,
    )

add_delay(
    T_COMPLETE,
    T_FIRST_BLUE,
    -0.43,
    f"First-detection delay: {T_FIRST_BLUE - T_COMPLETE:g} s",
)

add_delay(
    T_COMPLETE,
    T_ALL_BLUE,
    -0.94,
    f"Collective-detection delay: {T_ALL_BLUE - T_COMPLETE:g} s",
)

# ====================== RESOLUTION CHECK ======================

fig.canvas.draw()

print("Native photographic resolution at the plotted size:")
for key, photo_ax in photo_axes.items():
    box = photo_ax.get_position()
    width_in = box.width * fig.get_figwidth()
    height_in = box.height * fig.get_figheight()
    img = images[key]

    dpi_x = img.width / width_in
    dpi_y = img.height / height_in
    effective_dpi = min(dpi_x, dpi_y)

    print(
        f"  {IMAGE_FILES[key]}: "
        f"{img.width} x {img.height} px; "
        f"{width_in * 2.54:.2f} cm wide; "
        f"{effective_dpi:.0f} effective dpi"
    )

    if effective_dpi < 300:
        print(
            "    WARNING: use a higher-resolution original frame "
            "or reduce its printed size; upsampling will not add detail."
        )

# ====================== EXPORT ======================

pdf_path = OUTPUT_DIR / "Fig1_Dancing_LMC.pdf"
png_path = OUTPUT_DIR / "Fig1_Dancing_LMC_600dpi.png"

# Do not use bbox_inches="tight": retain the specified physical dimensions.
# PDF retains vector labels/lines and native embedded photo pixels.
fig.savefig(pdf_path, format="pdf")
fig.savefig(png_path, format="png", dpi=PNG_DPI)

plt.close(fig)

# ====================== LARGE COLAB PREVIEW ======================

# Preview dimensions are independent of publication dimensions.
encoded = base64.b64encode(png_path.read_bytes()).decode("ascii")

display(HTML(
    '<div style="overflow-x:auto; max-width:100%; '
    'border:1px solid #ddd; background:white;">'
    f'<img src="data:image/png;base64,{encoded}" '
    f'style="width:{PREVIEW_WIDTH_PX}px; max-width:none; height:auto;" '
    'alt="Dancing LMC experimental figure">'
    '</div>'
))

print(f"\nPublication size: {FIG_WIDTH_CM} x {FIG_HEIGHT_CM} cm")
print(f"PDF: {pdf_path}")
print(f"PNG: {png_path}")

if CONTROL_DURATION_S is None:
    print(
        "\nDRAFT: enter the verified control observation duration "
        "before using this figure in the manuscript."
    )

print(
    "\nNo physical scale bar was added because "
    "a verified image-to-distance calibration was not provided."
)

# Uncomment to download:
# files.download(str(pdf_path))
# files.download(str(png_path))

# %% [notebook cell 2]
import os
import string
import matplotlib.pyplot as plt
from PIL import Image

# ============================================================
# Input images
# Rows: task types
# Columns: experimental stages
# ============================================================

image_grid = [
    ["randomwalk1.png", "randomwalk2.png", "randomwalk3.png"],
    ["battery1.png",    "battery2.png",    "battery3.png"],
    ["voting1.png",     "voting2.png",     "voting3.png"],
]

row_labels = [
    "Random walk",
    "Battery",
    "Voting",
]

column_titles = [
    "Task in progress",
    "Current state complete;\nMeta-Completion not detected",
    "Meta-Completion detected",
]

# Confirm that every file exists
for row in image_grid:
    for filename in row:
        if not os.path.exists(filename):
            raise FileNotFoundError(f"Missing file: {filename}")

# ============================================================
# Figure layout
# ============================================================

fig, axes = plt.subplots(
    nrows=3,
    ncols=3,
    figsize=(15, 9.5),
)

# Reduce gaps while retaining space for titles and row labels
plt.subplots_adjust(
    left=0.095,
    right=0.995,
    top=0.91,
    bottom=0.025,
    wspace=0.025,
    hspace=0.055,
)

panel_labels = list(string.ascii_uppercase[:9])

for row_idx in range(3):
    for col_idx in range(3):
        ax = axes[row_idx, col_idx]

        image = Image.open(image_grid[row_idx][col_idx]).convert("RGB")
        ax.imshow(image)

        # Remove axes and borders
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)

        # Panel labels A–I
        panel_index = row_idx * 3 + col_idx
        ax.text(
            0.018,
            0.965,
            panel_labels[panel_index],
            transform=ax.transAxes,
            ha="left",
            va="top",
            fontsize=22,
            fontweight="bold",
            color="black",
            bbox=dict(
                boxstyle="square,pad=0.16",
                facecolor="white",
                edgecolor="none",
                alpha=0.88,
            ),
        )

        # Column headings appear only above the first row
        if row_idx == 0:
            ax.set_title(
                column_titles[col_idx],
                fontsize=16,
                fontweight="bold",
                pad=10,
            )

        # Row labels appear to the left of the first column
        if col_idx == 0:
            ax.set_ylabel(
                row_labels[row_idx],
                fontsize=17,
                fontweight="bold",
                rotation=90,
                labelpad=18,
            )

# ============================================================
# Export
# ============================================================

png_output = "kilobot_three_tasks_combined.png"
pdf_output = "kilobot_three_tasks_combined.pdf"

fig.savefig(
    png_output,
    dpi=600,
    bbox_inches="tight",
    pad_inches=0.03,
    facecolor="white",
)

fig.savefig(
    pdf_output,
    dpi=600,
    bbox_inches="tight",
    pad_inches=0.03,
    facecolor="white",
)

plt.show()

print(f"Saved: {png_output}")
print(f"Saved: {pdf_output}")

# %% [notebook cell 4]
import numpy as np
import matplotlib.pyplot as plt

from matplotlib.lines import Line2D
from scipy.stats import beta as beta_dist


plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "DejaVu Sans"],
    "mathtext.fontset": "dejavusans",
    "font.size": 18,
    "axes.labelsize": 20,
    "axes.titlesize": 26,
    "xtick.labelsize": 18,
    "ytick.labelsize": 18,
    "legend.fontsize": 14,
    "lines.linewidth": 1.5,
    "lines.markersize": 6,
    "axes.grid": False,
    "axes.linewidth": 1.2,
    "xtick.direction": "out",
    "ytick.direction": "out",
})


# ============================================================
# Parameters
# ============================================================
t_max = 200
r = 0.9
threshold = 0.99

# Panels B and C show all three tail probabilities.
tail_values = (0.1, 0.01, 0.001)

resolution = 201
rho = r

k1_vals = np.linspace(0, 1, resolution)
k2_vals = np.linspace(0, 1, resolution)
K1, K2 = np.meshgrid(k1_vals, k2_vals)
valid = K1 + K2 < 1.0 - 1e-12

k1 = K1[valid]
k2 = K2[valid]
n_points = len(k1)


# ============================================================
# Panel A: full completion
# ============================================================
K = k1 + k2
full_hit = np.zeros(n_points, dtype=bool)

for t in range(1, t_max + 1):
    mu_full = 1.0 - K**t
    full_hit |= mu_full >= threshold


# ============================================================
# Panels B and C: partial completion for every tail value
# ============================================================
a = k1 + rho * k2
b = 1.0 - k1 - k2
c = k1**2 + rho * k2**2
d = rho * (1.0 - rho) * k2**2

mu = np.zeros(n_points)
variance = np.zeros(n_points)

partial_hit_by_tail = {
    tail: np.zeros(n_points, dtype=bool) for tail in tail_values
}

for t in range(1, t_max + 1):
    variance_next = c * variance + d * mu**2
    mu_next = a * mu + b
    variance = variance_next
    mu = mu_next

    deterministic = variance == 0.0
    stochastic = ~deterministic

    admissible_beta = (
        (mu > 0.0)
        & (mu < 1.0)
        & (variance > 0.0)
        & (variance < mu * (1.0 - mu))
    )

    if np.any(stochastic & ~admissible_beta):
        raise ValueError(
            f"Round {t}: invalid moments for a Beta distribution."
        )

    quantiles = {
        tail: np.full(n_points, np.nan) for tail in tail_values
    }

    for tail in tail_values:
        quantiles[tail][deterministic] = mu[deterministic]

    if np.any(stochastic):
        mu_s = mu[stochastic]
        var_s = variance[stochastic]
        nu = mu_s * (1.0 - mu_s) / var_s - 1.0
        alpha = mu_s * nu
        beta_param = (1.0 - mu_s) * nu

        for tail in tail_values:
            quantiles[tail][stochastic] = beta_dist.ppf(
                1.0 - tail,
                alpha,
                beta_param,
            )

    for tail in tail_values:
        if not np.all(np.isfinite(quantiles[tail])):
            raise ValueError(
                f"Round {t}: non-finite quantile for tail={tail:g}."
            )
        partial_hit_by_tail[tail] |= quantiles[tail] >= threshold

    if t % 50 == 0:
        print(f"Checked rounds 1-{t} / {t_max}")


partial_no_hit_by_tail = {
    tail: ~partial_hit_by_tail[tail] for tail in tail_values
}

feasible_by_tail = {
    tail: full_hit & partial_no_hit_by_tail[tail]
    for tail in tail_values
}


# ============================================================
# Colours and plotting helpers
# ============================================================
GREEN = "#228B22"
RED = "#D62728"
GREY = "#D9D9D9"

# Draw broadest region first and narrowest region last.
PARTIAL_COLOURS = {
    0.1: "#F9E79F",
    0.01: "#F4D03F",
    0.001: "#D4AC0D",
}
FEASIBLE_COLOURS = {
    0.1: "#D7BDE2",
    0.01: "#A569BD",
    0.001: "#6C3483",
}

point_size = 9


def scatter_region(ax, mask, color, zorder=2):
    ax.scatter(
        k1[mask],
        k2[mask],
        c=color,
        marker="s",
        s=point_size,
        edgecolors="none",
        linewidths=0,
        alpha=1.0,
        rasterized=True,
        zorder=zorder,
    )


def legend_marker(color, label):
    return Line2D(
        [],
        [],
        marker="s",
        linestyle="none",
        markerfacecolor=color,
        markeredgecolor="none",
        markersize=11,
        label=label,
    )


def format_panel(ax, letter, title):
    ax.plot([0, 1], [1, 0], color="black", linewidth=1.8, zorder=5)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel(r"$k_1$")
    ax.set_ylabel(r"$k_2$")
    ax.set_title(title, pad=16)
    ticks = np.linspace(0, 1, 6)
    ax.set_xticks(ticks)
    ax.set_yticks(ticks)
    ax.grid(False, which="both")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.text(
        -0.13,
        1.06,
        letter,
        transform=ax.transAxes,
        fontsize=28,
        fontweight="bold",
        va="bottom",
        ha="left",
        clip_on=False,
    )


# ============================================================
# Figure
# ============================================================
fig, axes = plt.subplots(1, 3, figsize=(25, 10))
fig.subplots_adjust(
    left=0.05,
    right=0.99,
    bottom=0.29,
    top=0.90,
    wspace=0.28,
)


# Panel A
scatter_region(axes[0], ~full_hit, GREY)
scatter_region(axes[0], full_hit, GREEN)
format_panel(axes[0], "A", "Full completion")
axes[0].legend(
    handles=[
        legend_marker(GREEN, f"Threshold reached by round {t_max}"),
        legend_marker(GREY, "Threshold not reached"),
    ],
    loc="upper center",
    bbox_to_anchor=(0.5, -0.16),
    frameon=False,
    borderaxespad=0,
    fontsize=15,
)


# Panel B: nested partial-no-hit regions for all tail values.
# The red background means even the 90th percentile reaches the threshold.
scatter_region(axes[1], np.ones(n_points, dtype=bool), RED, zorder=1)
for zorder, tail in enumerate(tail_values, start=2):
    scatter_region(
        axes[1],
        partial_no_hit_by_tail[tail],
        PARTIAL_COLOURS[tail],
        zorder=zorder,
    )

format_panel(axes[1], "B", rf"Partial completion ($r={r:g}$)")
axes[1].legend(
    handles=[
        legend_marker(
            PARTIAL_COLOURS[tail],
            rf"$Q_t<0.99$ for all $t$; tail$={tail:g}$",
        )
        for tail in tail_values
    ]
    + [
        legend_marker(
            RED,
            r"$Q_t\geq0.99$ for tail$=0.1$",
        )
    ],
    loc="upper center",
    bbox_to_anchor=(0.5, -0.16),
    frameon=False,
    borderaxespad=0,
    fontsize=13,
)


# Panel C: nested feasible regions for all tail values.
scatter_region(axes[2], np.ones(n_points, dtype=bool), GREY, zorder=1)
for zorder, tail in enumerate(tail_values, start=2):
    scatter_region(
        axes[2],
        feasible_by_tail[tail],
        FEASIBLE_COLOURS[tail],
        zorder=zorder,
    )

format_panel(axes[2], "C", "Theoretical feasible region")
axes[2].legend(
    handles=[
        legend_marker(
            FEASIBLE_COLOURS[tail],
            rf"Both conditions; tail$={tail:g}$",
        )
        for tail in tail_values
    ]
    + [
        legend_marker(GREY, "At least one condition not satisfied"),
    ],
    loc="upper center",
    bbox_to_anchor=(0.5, -0.16),
    frameon=False,
    borderaxespad=0,
    fontsize=13,
)


plt.show()

# %% [notebook cell 5]
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import beta as beta_dist

# ============================================================
# Plot style
# ============================================================

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "DejaVu Sans"],
    "mathtext.fontset": "dejavusans",
    "font.size": 16,
    "axes.labelsize": 18,
    "axes.titlesize": 20,
    "xtick.labelsize": 15,
    "ytick.labelsize": 15,
    "legend.fontsize": 13,
    "lines.linewidth": 2.0,
    "axes.grid": False,
    "axes.linewidth": 1.2,
    "xtick.direction": "out",
    "ytick.direction": "out",
})


# ============================================================
# Parameters
# ============================================================

N = 100
m_complete = 99
rho = (m_complete - 1) / (N - 1)

T_max = 200
threshold = 0.99

tail_values = (0.1, 0.01, 0.001)

# Distribution snapshots requested
distribution_rounds = [100, 200]

# Number of independent swarm realisations
n_runs = 5000

master_seed = 20260909


# ============================================================
# Parameter sets
# ============================================================
#
# Replace these later with exact representative points from
# your theory/simulation map if needed.
# ============================================================

parameter_sets = [
    {
        "name": "Safe interior",
        "k1": 0.50,
        "k2": 0.43,
    },
    {
        "name": "Near boundary",
        "k1": 0.40,
        "k2": 0.55,
    },
    {
        "name": "Susceptible region",
        "k1": 0.20,
        "k2": 0.70,
    },
    {
        "name": "Neighbour-dominated",
        "k1": 0.10,
        "k2": 0.85,
    },
]


# ============================================================
# Theory: moment recurrence
# ============================================================

def theoretical_moments(k1, k2, T, rho):
    """
    Theory for a representative completed robot:

        mu_{t+1} = a mu_t + b
        v_{t+1}  = c v_t + d mu_t^2

    where
        a = k1 + rho*k2
        b = 1-k1-k2
        c = k1^2 + rho*k2^2
        d = rho(1-rho)k2^2
    """

    a = k1 + rho * k2
    b = 1.0 - k1 - k2
    c = k1**2 + rho * k2**2
    d = rho * (1.0 - rho) * k2**2

    mu = np.zeros(T + 1)
    var = np.zeros(T + 1)

    for t in range(T):
        var[t + 1] = (
            c * var[t]
            + d * mu[t]**2
        )

        mu[t + 1] = (
            a * mu[t]
            + b
        )

    return mu, var


# ============================================================
# Beta moment matching
# ============================================================

def get_beta_params(mu, var):
    """
    Return moment-matched Beta parameters.

    Returns None, None for deterministic point-mass cases.
    """

    if var <= 0.0:
        return None, None

    if not (0.0 < mu < 1.0):
        return None, None

    max_var = mu * (1.0 - mu)

    if not (0.0 < var < max_var):
        raise ValueError(
            f"Invalid Beta moments: mu={mu}, var={var}"
        )

    nu = max_var / var - 1.0

    alpha = mu * nu
    beta_param = (1.0 - mu) * nu

    return alpha, beta_param


# ============================================================
# Synchronous simulation
# ============================================================

def run_simulation(
    k1,
    k2,
    N,
    m_complete,
    T_max,
    n_runs,
    distribution_rounds,
    seed,
):
    """
    Matches the synchronous analytical reference condition.

    - m_complete robots permanently complete
    - remaining robots permanently unfinished
    - all beliefs initially zero
    - completed receivers sample uniformly from other N-1 robots
    - synchronous updates
    """

    rng = np.random.default_rng(seed)

    beliefs = np.zeros(
        (n_runs, N),
        dtype=np.float64,
    )

    empirical_mean = np.zeros(T_max + 1)
    empirical_var = np.zeros(T_max + 1)

    snapshots = {}

    receiver_indices = np.arange(m_complete)

    b = 1.0 - k1 - k2

    for t in range(1, T_max + 1):

        old = beliefs.copy()

        # ----------------------------------------------------
        # Sample one partner uniformly from the other N-1 robots
        # for every completed receiver in every realisation.
        # ----------------------------------------------------

        raw = rng.integers(
            0,
            N - 1,
            size=(n_runs, m_complete),
        )

        receivers = receiver_indices[None, :]

        partners = (
            raw
            + (raw >= receivers)
        )

        partner_beliefs = np.take_along_axis(
            old,
            partners,
            axis=1,
        )

        own_beliefs = old[:, :m_complete]

        # Synchronous update
        beliefs[:, :m_complete] = (
            k1 * own_beliefs
            + k2 * partner_beliefs
            + b
        )

        # Unfinished robots stay at zero
        beliefs[:, m_complete:] = 0.0

        completed_samples = beliefs[:, :m_complete].ravel()

        empirical_mean[t] = np.mean(completed_samples)

        empirical_var[t] = np.var(
            completed_samples,
            ddof=1,
        )

        if t in distribution_rounds:
            snapshots[t] = completed_samples.copy()

    return empirical_mean, empirical_var, snapshots


# ============================================================
# Run all parameter sets
# ============================================================

seed_sequence = np.random.SeedSequence(master_seed)
child_seeds = seed_sequence.spawn(len(parameter_sets))

results = {}

for idx, params in enumerate(parameter_sets):

    name = params["name"]
    k1 = params["k1"]
    k2 = params["k2"]

    if (
        k1 <= 0
        or k2 <= 0
        or k1 + k2 >= 1
    ):
        raise ValueError(
            f"Invalid parameter pair: "
            f"{name}, k1={k1}, k2={k2}"
        )

    print(
        f"Running {name}: "
        f"k1={k1:.2f}, "
        f"k2={k2:.2f}"
    )

    # Theory
    mu_theory, var_theory = theoretical_moments(
        k1=k1,
        k2=k2,
        T=T_max,
        rho=rho,
    )

    # Simulation
    (
        mu_sim,
        var_sim,
        snapshots,
    ) = run_simulation(
        k1=k1,
        k2=k2,
        N=N,
        m_complete=m_complete,
        T_max=T_max,
        n_runs=n_runs,
        distribution_rounds=distribution_rounds,
        seed=child_seeds[idx],
    )

    results[name] = {
        "k1": k1,
        "k2": k2,
        "mu_theory": mu_theory,
        "var_theory": var_theory,
        "mu_sim": mu_sim,
        "var_sim": var_sim,
        "snapshots": snapshots,
    }


# ============================================================
# Figure 1:
# Simulation mean belief vs theoretical mean belief
# ============================================================

fig, axes = plt.subplots(
    2,
    2,
    figsize=(14, 10),
    sharex=True,
    sharey=True,
)

axes = axes.ravel()

rounds = np.arange(T_max + 1)

for ax, params in zip(axes, parameter_sets):

    name = params["name"]
    result = results[name]

    k1 = result["k1"]
    k2 = result["k2"]

    ax.plot(
        rounds,
        result["mu_sim"],
        label="Simulation mean",
    )

    ax.plot(
        rounds,
        result["mu_theory"],
        linestyle="--",
        label="Theory mean",
    )

    ax.set_title(
        f"{name}\n"
        rf"$k_1={k1:.2f},\ k_2={k2:.2f}$"
    )

    ax.set_xlim(0, T_max)
    ax.set_ylim(0, 1)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


axes[0].set_ylabel(
    "Mean completed-robot belief"
)

axes[2].set_ylabel(
    "Mean completed-robot belief"
)

axes[2].set_xlabel(
    "Communication round"
)

axes[3].set_xlabel(
    "Communication round"
)

axes[0].legend(
    frameon=False
)

fig.suptitle(
    "Theoretical and simulated mean belief trajectories",
    fontsize=22,
)

fig.tight_layout()

plt.savefig(
    "S8_mean_belief_comparison.png",
    dpi=300,
    bbox_inches="tight",
)

plt.show()


# ============================================================
# Figure 2:
# Real belief distribution vs moment-matched Beta
#
# Rows:
# parameter sets
#
# Columns:
# T = 100 and T = 200
#
# Each panel:
# - simulation histogram
# - fitted Beta PDF
# - theta = 0.99
# - quantile positions for tau=0.1, 0.01, 0.001
# ============================================================

n_rows = len(parameter_sets)
n_cols = len(distribution_rounds)

fig, axes = plt.subplots(
    n_rows,
    n_cols,
    figsize=(12, 3.8 * n_rows),
    sharex=True,
)

if n_rows == 1:
    axes = np.array([axes])

x_grid = np.linspace(
    0.0001,
    0.9999,
    1500,
)

percentile_names = {
    0.1: "90th",
    0.01: "99th",
    0.001: "99.9th",
}

linestyles = {
    0.1: "--",
    0.01: "-.",
    0.001: ":",
}

for row_idx, params in enumerate(parameter_sets):

    name = params["name"]

    result = results[name]

    k1 = result["k1"]
    k2 = result["k2"]

    mu_theory = result["mu_theory"]
    var_theory = result["var_theory"]

    for col_idx, t in enumerate(distribution_rounds):

        ax = axes[row_idx, col_idx]

        samples = result["snapshots"][t]

        # ----------------------------------------------------
        # Empirical simulation distribution
        # ----------------------------------------------------

        ax.hist(
            samples,
            bins=70,
            density=True,
            alpha=0.45,
            label="Simulation belief distribution",
        )

        # ----------------------------------------------------
        # Moment-matched Beta
        # ----------------------------------------------------

        alpha, beta_param = get_beta_params(
            mu_theory[t],
            var_theory[t],
        )

        if alpha is not None:

            beta_pdf = beta_dist.pdf(
                x_grid,
                alpha,
                beta_param,
            )

            ax.plot(
                x_grid,
                beta_pdf,
                linewidth=2.2,
                label="Moment-matched Beta",
            )

            # ------------------------------------------------
            # Beta quantiles corresponding to the three tails
            # ------------------------------------------------

            for tail in tail_values:

                quantile = beta_dist.ppf(
                    1.0 - tail,
                    alpha,
                    beta_param,
                )

                ax.axvline(
                    quantile,
                    linestyle=linestyles[tail],
                    linewidth=1.6,
                    label=(
                        f"Beta {percentile_names[tail]} "
                        "percentile"
                    ),
                )

        else:

            ax.axvline(
                mu_theory[t],
                linewidth=2.2,
                label="Theory point mass",
            )

        # ----------------------------------------------------
        # Fixed robot-level detection threshold
        # ----------------------------------------------------

        ax.axvline(
            threshold,
            linestyle=":",
            linewidth=2.0,
            label=r"Detection threshold $\theta=0.99$",
        )

        ax.set_xlim(0, 1)

        if row_idx == 0:
            ax.set_title(
                f"Round {t}"
            )

        if col_idx == 0:
            ax.set_ylabel(
                f"{name}\nDensity"
            )

        if row_idx == n_rows - 1:
            ax.set_xlabel(
                r"Completed-robot belief $P_i^t$"
            )

        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)


# Only one legend for whole figure
handles, labels = axes[0, 0].get_legend_handles_labels()

fig.legend(
    handles,
    labels,
    loc="lower center",
    ncol=3,
    frameon=False,
    bbox_to_anchor=(0.5, -0.01),
)

fig.suptitle(
    "Empirical belief distributions and moment-matched Beta approximations",
    fontsize=22,
    y=0.995,
)

fig.tight_layout(
    rect=[0, 0.07, 1, 0.97]
)

plt.savefig(
    "S8_beta_distribution_T100_T200.png",
    dpi=300,
    bbox_inches="tight",
)

plt.show()


# ============================================================
# Optional Figure 3:
# Theory and simulation mean + variance
#
# Useful diagnostically, but probably not necessary in paper.
# ============================================================

fig, axes = plt.subplots(
    2,
    2,
    figsize=(14, 10),
    sharex=True,
)

axes = axes.ravel()

for ax, params in zip(axes, parameter_sets):

    name = params["name"]
    result = results[name]

    ax.plot(
        rounds,
        result["var_sim"],
        label="Simulation variance",
    )

    ax.plot(
        rounds,
        result["var_theory"],
        linestyle="--",
        label="Theory variance",
    )

    ax.set_title(
        f"{name}\n"
        rf"$k_1={result['k1']:.2f}, "
        rf"k_2={result['k2']:.2f}$"
    )

    ax.set_xlim(0, T_max)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


axes[0].set_ylabel(
    "Variance of completed-robot belief"
)

axes[2].set_ylabel(
    "Variance of completed-robot belief"
)

axes[2].set_xlabel(
    "Communication round"
)

axes[3].set_xlabel(
    "Communication round"
)

axes[0].legend(
    frameon=False
)

fig.suptitle(
    "Theoretical and simulated belief variance",
    fontsize=22,
)

fig.tight_layout()

plt.savefig(
    "S8_variance_comparison.png",
    dpi=300,
    bbox_inches="tight",
)

plt.show()


# ============================================================
# Print quantitative checks
# ============================================================

print("\n")
print("=" * 90)
print("THEORY / SIMULATION COMPARISON")
print("=" * 90)

for params in parameter_sets:

    name = params["name"]

    result = results[name]

    print(f"\n{name}")
    print(
        f"k1={result['k1']:.3f}, "
        f"k2={result['k2']:.3f}"
    )

    for t in distribution_rounds:

        samples = result["snapshots"][t]

        empirical_mu = np.mean(samples)
        empirical_var = np.var(
            samples,
            ddof=1,
        )

        theory_mu = result[
            "mu_theory"
        ][t]

        theory_var = result[
            "var_theory"
        ][t]

        print(
            f"\nRound {t}:"
        )

        print(
            f"  mean:"
            f" simulation={empirical_mu:.6f},"
            f" theory={theory_mu:.6f},"
            f" error={empirical_mu-theory_mu:+.6f}"
        )

        print(
            f"  variance:"
            f" simulation={empirical_var:.6f},"
            f" theory={theory_var:.6f},"
            f" error={empirical_var-theory_var:+.6f}"
        )

        alpha, beta_param = get_beta_params(
            theory_mu,
            theory_var,
        )

        if alpha is not None:

            for tail in tail_values:

                q = beta_dist.ppf(
                    1.0 - tail,
                    alpha,
                    beta_param,
                )

                print(
                    f"  tail={tail:g}: "
                    f"Beta quantile={q:.6f}, "
                    f"compare with theta={threshold:.2f}"
                )


print("\nFinished.")
print("Saved:")
print("  S8_mean_belief_comparison.png")
print("  S8_beta_distribution_T100_T200.png")
print("  S8_variance_comparison.png")

# %% [notebook cell 6]
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import beta as beta_dist


# ============================================================
# Plot style
# ============================================================

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "DejaVu Sans"],
    "mathtext.fontset": "dejavusans",
    "font.size": 15,
    "axes.labelsize": 17,
    "axes.titlesize": 19,
    "xtick.labelsize": 14,
    "ytick.labelsize": 14,
    "legend.fontsize": 12,
    "lines.linewidth": 2.0,
    "axes.grid": False,
    "axes.linewidth": 1.2,
    "xtick.direction": "out",
    "ytick.direction": "out",
})


# ============================================================
# Global parameters
# ============================================================

N = 100

T_max = 200

threshold = 0.99

tail_values = (
    0.1,
    0.01,
    0.001,
)

distribution_rounds = [
    100,
    200,
]

# Number of independent swarm realisations
n_runs = 5000

master_seed = 20260909

# Two completed fractions examined in S8
r_values = [
    0.90,
    0.99,
]


# ============================================================
# Representative parameter sets
# ============================================================

parameter_sets = [
    {
        "name": "Safe interior",
        "k1": 0.50,
        "k2": 0.43,
    },
    {
        "name": "Near boundary",
        "k1": 0.40,
        "k2": 0.55,
    },
]


# ============================================================
# Theory: mean and variance recurrence
# ============================================================

def theoretical_moments(k1, k2, T, rho):
    """
    Analytical reference model for a representative completed robot.

    mu_{t+1} = a mu_t + b

    v_{t+1} = c v_t + d mu_t^2

    where

    a = k1 + rho*k2
    b = 1-k1-k2
    c = k1^2 + rho*k2^2
    d = rho(1-rho)k2^2
    """

    a = k1 + rho * k2

    b = 1.0 - k1 - k2

    c = (
        k1**2
        + rho * k2**2
    )

    d = (
        rho
        * (1.0 - rho)
        * k2**2
    )

    mu = np.zeros(T + 1)

    var = np.zeros(T + 1)

    for t in range(T):

        var[t + 1] = (
            c * var[t]
            + d * mu[t]**2
        )

        mu[t + 1] = (
            a * mu[t]
            + b
        )

    return mu, var


# ============================================================
# Beta moment matching
# ============================================================

def beta_parameters(mu, var):
    """
    Convert predicted mean/variance to moment-matched Beta parameters.

    Returns:
        alpha, beta_param

    If variance is zero, returns None, None.
    """

    if var <= 0.0:
        return None, None

    if not (
        0.0 < mu < 1.0
    ):
        return None, None

    max_var = (
        mu
        * (1.0 - mu)
    )

    if not (
        0.0 < var < max_var
    ):
        raise ValueError(
            f"Invalid Beta moments: "
            f"mu={mu}, var={var}"
        )

    nu = (
        max_var / var
        - 1.0
    )

    alpha = (
        mu * nu
    )

    beta_param = (
        (1.0 - mu)
        * nu
    )

    return alpha, beta_param


# ============================================================
# Synchronous simulation
# ============================================================

def run_simulation(
    k1,
    k2,
    N,
    m_complete,
    T_max,
    n_runs,
    distribution_rounds,
    seed,
):
    """
    Simulation conditions match the analytical reference model:

    - first m_complete robots are permanently complete
    - remaining robots are permanently unfinished
    - all initial beliefs are zero
    - synchronous updates
    - each completed robot samples one uniformly random other robot
    - unfinished robots remain at zero belief
    """

    rng = np.random.default_rng(
        seed
    )

    beliefs = np.zeros(
        (n_runs, N),
        dtype=np.float64,
    )

    empirical_mean = np.zeros(
        T_max + 1
    )

    empirical_var = np.zeros(
        T_max + 1
    )

    snapshots = {}

    receiver_indices = np.arange(
        m_complete
    )

    b = (
        1.0
        - k1
        - k2
    )

    for t in range(
        1,
        T_max + 1,
    ):

        old = beliefs.copy()

        # ----------------------------------------------------
        # Sample one partner per completed receiver.
        #
        # raw is sampled from [0, N-2].
        # Then shifted so receiver cannot sample itself.
        # ----------------------------------------------------

        raw = rng.integers(
            0,
            N - 1,
            size=(
                n_runs,
                m_complete,
            ),
        )

        receivers = (
            receiver_indices[
                None,
                :
            ]
        )

        partners = (
            raw
            + (
                raw
                >= receivers
            )
        )

        partner_beliefs = (
            np.take_along_axis(
                old,
                partners,
                axis=1,
            )
        )

        own_old = (
            old[
                :,
                :m_complete
            ]
        )

        # ----------------------------------------------------
        # Synchronous LMC update for completed robots
        # ----------------------------------------------------

        beliefs[
            :,
            :m_complete
        ] = (
            k1 * own_old
            + k2 * partner_beliefs
            + b
        )

        # ----------------------------------------------------
        # Unfinished robots remain fixed at zero
        # ----------------------------------------------------

        beliefs[
            :,
            m_complete:
        ] = 0.0

        completed_samples = (
            beliefs[
                :,
                :m_complete
            ].ravel()
        )

        empirical_mean[t] = (
            np.mean(
                completed_samples
            )
        )

        empirical_var[t] = (
            np.var(
                completed_samples,
                ddof=1,
            )
        )

        if (
            t
            in distribution_rounds
        ):

            snapshots[t] = (
                completed_samples.copy()
            )

    return (
        empirical_mean,
        empirical_var,
        snapshots,
    )


# ============================================================
# Run all simulations
# ============================================================

results = {}

seed_sequence = (
    np.random.SeedSequence(
        master_seed
    )
)

child_seeds = (
    seed_sequence.spawn(
        len(r_values)
        * len(parameter_sets)
    )
)

seed_counter = 0


for r in r_values:

    m_complete = int(
        round(
            r * N
        )
    )

    rho = (
        (m_complete - 1)
        / (N - 1)
    )

    results[r] = {}

    for params in parameter_sets:

        name = params["name"]

        k1 = params["k1"]

        k2 = params["k2"]

        print(
            f"Running "
            f"r={r:.2f}, "
            f"{name}, "
            f"k1={k1:.2f}, "
            f"k2={k2:.2f}"
        )

        # ----------------------------------------------------
        # Theory
        # ----------------------------------------------------

        (
            mu_theory,
            var_theory,
        ) = theoretical_moments(
            k1=k1,
            k2=k2,
            T=T_max,
            rho=rho,
        )

        # ----------------------------------------------------
        # Simulation
        # ----------------------------------------------------

        (
            mu_sim,
            var_sim,
            snapshots,
        ) = run_simulation(
            k1=k1,
            k2=k2,
            N=N,
            m_complete=m_complete,
            T_max=T_max,
            n_runs=n_runs,
            distribution_rounds=distribution_rounds,
            seed=child_seeds[
                seed_counter
            ],
        )

        seed_counter += 1

        results[r][name] = {
            "k1": k1,
            "k2": k2,
            "rho": rho,
            "m_complete": m_complete,
            "mu_theory": mu_theory,
            "var_theory": var_theory,
            "mu_sim": mu_sim,
            "var_sim": var_sim,
            "snapshots": snapshots,
        }


# ============================================================
# FIGURE Sx
#
# Theory vs simulation:
# mean and variance
#
# Columns:
# Safe interior
# Near boundary
#
# Rows:
# 1. r=0.90 mean
# 2. r=0.90 variance
# 3. r=0.99 mean
# 4. r=0.99 variance
# ============================================================

fig, axes = plt.subplots(
    4,
    2,
    figsize=(11, 13),
    sharex=True,
)

rounds = np.arange(
    T_max + 1
)


for col, params in enumerate(
    parameter_sets
):

    name = params["name"]

    # ========================================================
    # r = 0.90
    # ========================================================

    result = (
        results[
            0.90
        ][
            name
        ]
    )

    # Mean
    axes[
        0,
        col
    ].plot(
        rounds,
        result["mu_sim"],
        label="Simulation mean",
    )

    axes[
        0,
        col
    ].plot(
        rounds,
        result["mu_theory"],
        linestyle="--",
        label="Theory mean",
    )

    axes[
        0,
        col
    ].set_title(
        f"{name}\n"
        rf"$k_1={result['k1']:.2f}, "
        rf"k_2={result['k2']:.2f}$"
    )

    # Variance
    axes[
        1,
        col
    ].plot(
        rounds,
        result["var_sim"],
        label="Simulation variance",
    )

    axes[
        1,
        col
    ].plot(
        rounds,
        result["var_theory"],
        linestyle="--",
        label="Theory variance",
    )

    # ========================================================
    # r = 0.99
    # ========================================================

    result = (
        results[
            0.99
        ][
            name
        ]
    )

    # Mean
    axes[
        2,
        col
    ].plot(
        rounds,
        result["mu_sim"],
        label="Simulation mean",
    )

    axes[
        2,
        col
    ].plot(
        rounds,
        result["mu_theory"],
        linestyle="--",
        label="Theory mean",
    )

    # Variance
    axes[
        3,
        col
    ].plot(
        rounds,
        result["var_sim"],
        label="Simulation variance",
    )

    axes[
        3,
        col
    ].plot(
        rounds,
        result["var_theory"],
        linestyle="--",
        label="Theory variance",
    )


# ------------------------------------------------------------
# Row labels
# ------------------------------------------------------------

axes[
    0,
    0
].set_ylabel(
    r"$r=0.90$"
    + "\nMean belief"
)

axes[
    1,
    0
].set_ylabel(
    r"$r=0.90$"
    + "\nBelief variance"
)

axes[
    2,
    0
].set_ylabel(
    r"$r=0.99$"
    + "\nMean belief"
)

axes[
    3,
    0
].set_ylabel(
    r"$r=0.99$"
    + "\nBelief variance"
)


# ------------------------------------------------------------
# X labels
# ------------------------------------------------------------

for col in range(2):

    axes[
        3,
        col
    ].set_xlabel(
        "Communication round"
    )


# ------------------------------------------------------------
# Formatting
# ------------------------------------------------------------

for row in range(4):

    for col in range(2):

        axes[
            row,
            col
        ].set_xlim(
            0,
            T_max
        )

        axes[
            row,
            col
        ].spines[
            "top"
        ].set_visible(
            False
        )

        axes[
            row,
            col
        ].spines[
            "right"
        ].set_visible(
            False
        )


# Mean panels share [0,1]
for col in range(2):

    axes[
        0,
        col
    ].set_ylim(
        0,
        1
    )

    axes[
        2,
        col
    ].set_ylim(
        0,
        1
    )


# ------------------------------------------------------------
# Legends
# ------------------------------------------------------------

mean_handles, mean_labels = (
    axes[
        0,
        0
    ].get_legend_handles_labels()
)

variance_handles, variance_labels = (
    axes[
        1,
        0
    ].get_legend_handles_labels()
)

fig.legend(
    mean_handles
    + variance_handles,
    mean_labels
    + variance_labels,
    loc="upper center",
    ncol=4,
    frameon=False,
    bbox_to_anchor=(
        0.5,
        0.965
    ),
)


fig.suptitle(
    "Agreement between theoretical and simulated belief moments",
    fontsize=22,
    y=0.995,
)


fig.tight_layout(
    rect=[
        0,
        0,
        1,
        0.93,
    ]
)


plt.savefig(
    "Fig_Sx_moment_validation.png",
    dpi=300,
    bbox_inches="tight",
)


plt.show()


# ============================================================
# FIGURE Sy
#
# Empirical belief distribution vs moment-matched Beta
#
# Generate one figure for each completed fraction:
# r=0.90
# r=0.99
#
# Rows:
# Safe interior
# Near boundary
#
# Columns:
# T=100
# T=200
# ============================================================


percentile_names = {
    0.1: "90th percentile",
    0.01: "99th percentile",
    0.001: "99.9th percentile",
}


linestyles = {
    0.1: "--",
    0.01: "-.",
    0.001: ":",
}


x_grid = np.linspace(
    0.0001,
    0.9999,
    1500,
)


for r in r_values:

    fig, axes = plt.subplots(
        2,
        2,
        figsize=(11, 8),
        sharex=True,
    )


    for row, params in enumerate(
        parameter_sets
    ):

        name = params["name"]

        result = (
            results[
                r
            ][
                name
            ]
        )


        for col, t in enumerate(
            distribution_rounds
        ):

            ax = axes[
                row,
                col
            ]

            samples = (
                result[
                    "snapshots"
                ][
                    t
                ]
            )

            # ------------------------------------------------
            # Empirical simulation distribution
            # ------------------------------------------------

            ax.hist(
                samples,
                bins=70,
                density=True,
                alpha=0.45,
                label=(
                    "Simulation belief "
                    "distribution"
                ),
            )


            # ------------------------------------------------
            # Theory moments at this round
            # ------------------------------------------------

            mu = (
                result[
                    "mu_theory"
                ][
                    t
                ]
            )

            var = (
                result[
                    "var_theory"
                ][
                    t
                ]
            )


            (
                alpha,
                beta_param,
            ) = beta_parameters(
                mu,
                var,
            )


            # ------------------------------------------------
            # Moment-matched Beta distribution
            # ------------------------------------------------

            if (
                alpha
                is not None
            ):

                pdf = beta_dist.pdf(
                    x_grid,
                    alpha,
                    beta_param,
                )

                ax.plot(
                    x_grid,
                    pdf,
                    linewidth=2.2,
                    label=(
                        "Moment-matched Beta"
                    ),
                )


                # --------------------------------------------
                # Quantiles corresponding to the three tails
                # --------------------------------------------

                for tail in tail_values:

                    quantile = (
                        beta_dist.ppf(
                            1.0 - tail,
                            alpha,
                            beta_param,
                        )
                    )

                    ax.axvline(
                        quantile,
                        linestyle=(
                            linestyles[
                                tail
                            ]
                        ),
                        linewidth=1.7,
                        label=(
                            f"Beta "
                            f"{percentile_names[tail]}"
                        ),
                    )


            # ------------------------------------------------
            # Fixed detection threshold
            # ------------------------------------------------

            ax.axvline(
                threshold,
                linestyle=":",
                linewidth=2.2,
                label=(
                    r"Detection threshold "
                    r"$\theta=0.99$"
                ),
            )


            # ------------------------------------------------
            # Formatting
            # ------------------------------------------------

            ax.set_xlim(
                0,
                1
            )

            if (
                row == 0
            ):

                ax.set_title(
                    f"Round {t}"
                )

            if (
                col == 0
            ):

                ax.set_ylabel(
                    f"{name}\nDensity"
                )

            if (
                row
                == len(
                    parameter_sets
                ) - 1
            ):

                ax.set_xlabel(
                    r"Completed-robot belief "
                    r"$P_i^t$"
                )


            ax.spines[
                "top"
            ].set_visible(
                False
            )

            ax.spines[
                "right"
            ].set_visible(
                False
            )


    handles, labels = (
        axes[
            0,
            0
        ].get_legend_handles_labels()
    )


    fig.legend(
        handles,
        labels,
        loc="lower center",
        ncol=3,
        frameon=False,
        bbox_to_anchor=(
            0.5,
            0.01
        ),
    )


    fig.suptitle(
        rf"Empirical belief distributions and "
        rf"moment-matched Beta approximation "
        rf"($r={r:.2f}$)",
        fontsize=22,
        y=0.995,
    )


    fig.tight_layout(
        rect=[
            0,
            0.10,
            1,
            0.95,
        ]
    )


    plt.savefig(
        (
            "Fig_Sy_beta_distribution_"
            f"r{int(round(r * 100)):02d}.png"
        ),
        dpi=300,
        bbox_inches="tight",
    )


    plt.show()


# ============================================================
# FIGURE Sz
#
# Tail sensitivity:
#
# U_{T,tau} versus completed fraction r
#
# Main parameter pair:
# Safe interior
#
# Compare T=100 and T=200
# ============================================================

r_sweep = np.arange(
    0.90,
    1.00,
    0.01,
)


# Use the main reference parameter pair
k1_tail = 0.50
k2_tail = 0.43


fig, axes = plt.subplots(
    1,
    2,
    figsize=(13, 5.5),
    sharey=True,
)


for ax, T_eval in zip(
    axes,
    distribution_rounds,
):

    quantile_curves = {
        tail: []
        for tail in tail_values
    }


    for r in r_sweep:

        m_complete = int(
            round(
                r * N
            )
        )

        rho = (
            (m_complete - 1)
            / (N - 1)
        )


        (
            mu,
            var,
        ) = theoretical_moments(
            k1=k1_tail,
            k2=k2_tail,
            T=T_eval,
            rho=rho,
        )


        (
            alpha,
            beta_param,
        ) = beta_parameters(
            mu[T_eval],
            var[T_eval],
        )


        for tail in tail_values:

            if (
                alpha
                is None
            ):

                quantile = (
                    mu[
                        T_eval
                    ]
                )

            else:

                quantile = (
                    beta_dist.ppf(
                        1.0 - tail,
                        alpha,
                        beta_param,
                    )
                )


            quantile_curves[
                tail
            ].append(
                quantile
            )


    for tail in tail_values:

        ax.plot(
            r_sweep,
            quantile_curves[
                tail
            ],
            marker="o",
            label=(
                percentile_names[
                    tail
                ]
            ),
        )


    ax.axhline(
        threshold,
        linestyle=":",
        linewidth=2.2,
        label=(
            r"Detection threshold "
            r"$\theta=0.99$"
        ),
    )


    ax.set_title(
        f"Round {T_eval}"
    )


    ax.set_xlabel(
        "Completed fraction $r$"
    )


    ax.set_xlim(
        0.90,
        0.99,
    )


    ax.set_ylim(
        0,
        1.02,
    )


    ax.spines[
        "top"
    ].set_visible(
        False
    )


    ax.spines[
        "right"
    ].set_visible(
        False
    )


axes[
    0
].set_ylabel(
    r"Beta upper quantile "
    r"$U_{T,\tau}$"
)


axes[
    0
].legend(
    frameon=False
)


fig.suptitle(
    rf"Upper-tail sensitivity for "
    rf"$k_1={k1_tail:.2f}, "
    rf"k_2={k2_tail:.2f}$",
    fontsize=22,
)


fig.tight_layout()


plt.savefig(
    "Fig_Sz_tail_sensitivity.png",
    dpi=300,
    bbox_inches="tight",
)


plt.show()


# ============================================================
# Numerical summary
# ============================================================

print("\n")
print(
    "=" * 90
)

print(
    "THEORY / SIMULATION SUMMARY"
)

print(
    "=" * 90
)


for r in r_values:

    print(
        f"\nCompleted fraction "
        f"r={r:.2f}"
    )


    for params in parameter_sets:

        name = params["name"]

        result = (
            results[
                r
            ][
                name
            ]
        )


        print(
            f"\n{name}"
        )

        print(
            f"k1={result['k1']:.2f}, "
            f"k2={result['k2']:.2f}"
        )


        for t in distribution_rounds:

            mu_sim = (
                result[
                    "mu_sim"
                ][
                    t
                ]
            )

            mu_theory = (
                result[
                    "mu_theory"
                ][
                    t
                ]
            )


            var_sim = (
                result[
                    "var_sim"
                ][
                    t
                ]
            )

            var_theory = (
                result[
                    "var_theory"
                ][
                    t
                ]
            )


            print(
                f"\n  Round {t}:"
            )


            print(
                f"    Mean "
                f"simulation={mu_sim:.6f}, "
                f"theory={mu_theory:.6f}, "
                f"error="
                f"{mu_sim-mu_theory:+.6e}"
            )


            print(
                f"    Variance "
                f"simulation={var_sim:.6f}, "
                f"theory={var_theory:.6f}, "
                f"error="
                f"{var_sim-var_theory:+.6e}"
            )


            (
                alpha,
                beta_param,
            ) = beta_parameters(
                mu_theory,
                var_theory,
            )


            if (
                alpha
                is not None
            ):

                for tail in tail_values:

                    quantile = (
                        beta_dist.ppf(
                            1.0 - tail,
                            alpha,
                            beta_param,
                        )
                    )


                    print(
                        f"    tau={tail:g}: "
                        f"U={quantile:.6f}, "
                        f"theta={threshold:.2f}"
                    )


print("\nFinished.")

print(
    "Saved:"
)

print(
    "  Fig_Sx_moment_validation.png"
)

print(
    "  Fig_Sy_beta_distribution_r90.png"
)

print(
    "  Fig_Sy_beta_distribution_r99.png"
)

print(
    "  Fig_Sz_tail_sensitivity.png"
)

# %% [notebook cell 8]
# from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, to_rgba
from matplotlib.lines import Line2D
from matplotlib.ticker import MaxNLocator
from scipy.stats import beta as beta_dist


N = 100
THETA = 0.99
RUNS_MAP = 10
RUNS_BAR = 1000
SEED = 20260921


def parameter_grid():
    values = np.linspace(0.0, 1.0, 101)
    k1_grid, k2_grid = np.meshgrid(values, values)
    valid = (k1_grid > 0) & (k2_grid > 0) & (k1_grid + k2_grid < 1)
    return k1_grid, k2_grid, valid


def unfiltered_parameter_maps():
    """Agent simulations for panels A and B using a single crossing."""
    k1_grid, k2_grid, valid = parameter_grid()
    k1 = k1_grid[valid]
    k2 = k2_grid[valid]
    n_points = k1.size
    point_index = np.arange(n_points)[:, None]
    trial_index = np.arange(RUNS_MAP)[None, :]
    rng = np.random.default_rng(SEED)

    sim_full = np.zeros(n_points, dtype=bool)
    sim_partial_hit = np.zeros(n_points, dtype=bool)

    for completed_count, full_condition in [(N, True), (90, False)]:
        beliefs = np.zeros((n_points, RUNS_MAP, N), dtype=np.float32)
        ever = np.zeros((n_points, RUNS_MAP, N), dtype=bool)
        states = np.zeros(N, dtype=np.float32)
        states[:completed_count] = 1.0

        for _ in range(200):
            for i in range(N):
                partners = rng.integers(0, N - 1, size=(n_points, RUNS_MAP))
                partners += partners >= i
                if states[i] == 0:
                    beliefs[:, :, i] = 0.0
                else:
                    neighbor = beliefs[point_index, trial_index, partners]
                    beliefs[:, :, i] = (
                        k1[:, None] * beliefs[:, :, i]
                        + k2[:, None] * neighbor
                        + (1.0 - k1 - k2)[:, None]
                    )
                ever[:, :, i] |= beliefs[:, :, i] >= THETA

        if full_condition:
            # Every robot must reach the threshold in every replicate.
            sim_full = ever.all(axis=2).all(axis=1)
        else:
            # One crossing by any robot in any replicate is a premature hit.
            sim_partial_hit = ever.any(axis=2).any(axis=1)

    full_map = np.zeros(valid.shape, dtype=bool)
    partial_map = np.zeros(valid.shape, dtype=bool)
    full_map[valid] = sim_full
    partial_map[valid] = sim_partial_hit
    return k1_grid, k2_grid, valid, full_map, partial_map


def theory_parameter_maps(k1_grid, k2_grid, valid):
    """Analytical classifications used in comparison panels C and D."""
    k1 = k1_grid[valid]
    k2 = k2_grid[valid]
    theory_full_values = 1.0 - (k1 + k2) ** 200 >= THETA

    rho = 89.0 / 99.0
    a = k1 + rho * k2
    b = 1.0 - k1 - k2
    c = k1**2 + rho * k2**2
    d = rho * (1.0 - rho) * k2**2
    mu = np.zeros_like(k1)
    variance = np.zeros_like(k1)
    theory_partial_values = np.zeros_like(k1, dtype=bool)

    for _ in range(200):
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
                0.90, mu_s * nu, (1.0 - mu_s) * nu
            )
        theory_partial_values |= quantile >= THETA

    theory_full = np.zeros(valid.shape, dtype=bool)
    theory_partial = np.zeros(valid.shape, dtype=bool)
    theory_full[valid] = theory_full_values
    theory_partial[valid] = theory_partial_values
    return theory_full, theory_partial


def confirmation_parameter_map():
    """Partial completion (m=90), T=200, ten consecutive rounds."""
    k1_grid, k2_grid, valid = parameter_grid()
    rows, cols = np.where(valid)
    k1 = k1_grid[valid]
    k2 = k2_grid[valid]
    n_points = k1.size

    rng = np.random.default_rng(SEED + 10)
    beliefs = np.zeros((n_points, RUNS_MAP, N), dtype=np.float32)
    consecutive = np.zeros((n_points, RUNS_MAP, N), dtype=np.uint8)
    transitioned = np.zeros((n_points, RUNS_MAP), dtype=bool)
    state = np.zeros(N, dtype=np.float32)
    state[:90] = 1.0
    point_index = np.arange(n_points)[:, None]
    trial_index = np.arange(RUNS_MAP)[None, :]

    for _ in range(200):
        for i in range(N):
            partners = rng.integers(0, N - 1, size=(n_points, RUNS_MAP))
            partners += partners >= i
            if state[i] == 0:
                beliefs[:, :, i] = 0
            else:
                neighbor = beliefs[point_index, trial_index, partners]
                beliefs[:, :, i] = (
                    k1[:, None] * beliefs[:, :, i]
                    + k2[:, None] * neighbor
                    + (1.0 - k1 - k2)[:, None]
                )
            above = beliefs[:, :, i] >= THETA
            consecutive[:, :, i] = np.where(
                above, np.minimum(consecutive[:, :, i] + 1, 10), 0
            )
            transitioned |= consecutive[:, :, i] >= 10

    hit = transitioned.any(axis=1)
    result = np.full(valid.shape, np.nan)
    result[rows, cols] = hit.astype(float)
    return k1_grid, k2_grid, valid, result


def premature_counts(k1=0.40, k2=0.53):
    """Run-level counts with one unfinished robot for d=1 and d=10."""
    horizons = np.asarray([200, 600, 2000])
    out = np.zeros((2, len(horizons)), dtype=int)
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
            h_index = int(np.where(horizons == round_number)[0][0])
            out[0, h_index] = single_hit.sum()
            out[1, h_index] = confirmed_hit.sum()

    return horizons, out


def draw_classes(ax, valid, masks, colors):
    for mask, color in zip(masks, colors):
        selected = valid & mask
        rgba = np.zeros((*valid.shape, 4), dtype=float)
        rgba[selected] = to_rgba(color)
        ax.imshow(rgba, origin="lower", extent=[-0.005, 1.005, -0.005, 1.005],
                  interpolation="nearest", aspect="equal")


def style_parameter_axis(ax, title):
    boundary = np.linspace(0.0, 1.0, 200)
    ax.plot(boundary, 1.0 - boundary, color="black", linewidth=1.2)
    ax.set(xlim=(0, 1), ylim=(0, 1), xlabel=r"$k_1$", ylabel=r"$k_2$",
           title=title)


def square_legend(ax, entries):
    handles = [
        Line2D([], [], marker="s", linestyle="none", markersize=8,
               markerfacecolor=color, markeredgecolor="none", label=label)
        for color, label in entries
    ]
    ax.legend(handles=handles, frameon=False, loc="upper center",
              bbox_to_anchor=(0.5, -0.18), fontsize=12)


def plot_panels(simulation_data, theory_data, confirmation_data, bar_data):
    k1_grid, k2_grid, valid, sim_full, sim_partial = simulation_data
    theory_full, theory_partial = theory_data
    _, _, _, confirmation_map = confirmation_data
    horizons, counts = bar_data
    plt.rcParams.update({
        "font.family": "sans-serif", "font.sans-serif": ["Arial", "DejaVu Sans"],
        "mathtext.fontset": "dejavusans", "font.size": 18,
        "axes.titlesize": 24, "axes.labelsize": 22,
        "xtick.labelsize": 18, "ytick.labelsize": 18,
        "legend.fontsize": 18,
    })
    fig, axes = plt.subplots(3, 2, figsize=(18, 22))
    fig.subplots_adjust(left=0.08, right=0.98, top=0.97, bottom=0.06,
                        hspace=0.62, wspace=0.32)
    ax_a, ax_b, ax_c, ax_d, ax_e, ax_f = axes.flat

    draw_classes(ax_a, valid, [~sim_full, sim_full], ["#D9D9D9", "#228B22"])
    style_parameter_axis(ax_a, "Simulation: full completion")
    square_legend(ax_a, [("#228B22", "All robots reach 0.99"),
                         ("#D9D9D9", "Not all robots reach 0.99")])

    draw_classes(ax_b, valid, [~sim_partial, sim_partial], ["#F2D93B", "#D62728"])
    style_parameter_axis(ax_b, r"Simulation: $r=0.9$")
    square_legend(ax_b, [("#F2D93B", "No premature event observed"),
                         ("#D62728", "Premature event observed")])

    full_both = theory_full & sim_full
    full_neither = ~theory_full & ~sim_full
    full_theory_only = theory_full & ~sim_full
    full_sim_only = ~theory_full & sim_full
    draw_classes(ax_c, valid,
                 [full_neither, full_both, full_theory_only, full_sim_only],
                 ["#D9D9D9", "#228B22", "#111111", "#1F77B4"])
    style_parameter_axis(ax_c, "Full-completion comparison")
    square_legend(ax_c, [("#228B22", "Both reach"),
                         ("#D9D9D9", "Neither reaches"),
                         ("#111111", "Theory only"),
                         ("#1F77B4", "Simulation only")])

    partial_both = theory_partial & sim_partial
    partial_neither = ~theory_partial & ~sim_partial
    partial_theory_only = theory_partial & ~sim_partial
    partial_sim_only = ~theory_partial & sim_partial
    draw_classes(ax_d, valid,
                 [partial_neither, partial_both,
                  partial_theory_only, partial_sim_only],
                 ["#F2D93B", "#D62728", "#111111", "#1F77B4"])
    style_parameter_axis(ax_d, "Partial-completion comparison")
    square_legend(ax_d, [("#F2D93B", "Neither reaches 0.99"),
                         ("#D62728", "Both reach 0.99"),
                         ("#111111", "Theory only reaches 0.99"),
                         ("#1F77B4", "Simulation only reaches 0.99")])

    masked = np.ma.masked_invalid(confirmation_map)
    ax_e.imshow(masked, origin="lower", extent=[-0.005, 1.005, -0.005, 1.005],
                interpolation="nearest", cmap=ListedColormap(["#F2D93B", "#D62728"]),
                vmin=0, vmax=1, aspect="equal")
    x = np.linspace(0, 1, 200)
    ax_e.plot(x, 1-x, color="black", lw=1.2)
    ax_e.set(xlim=(0,1), ylim=(0,1), xlabel=r"$k_1$", ylabel=r"$k_2$",
             title="10-round confirmation: $r=0.9$")
    square_legend(ax_e, [('#F2D93B', 'No premature transition observed'),
                         ('#D62728', 'Premature transition observed')])

    positions = np.arange(len(horizons)); width=0.36
    bars1=ax_f.bar(positions-width/2, counts[0], width, color="#D62728", label="Single crossing")
    bars2=ax_f.bar(positions+width/2, counts[1], width, color="#1F77B4", label="10-round confirmation")
    ax_f.set_xticks(positions, horizons)
    ax_f.set_xlabel("Observation horizon, $T$")
    ax_f.set_ylabel("Runs with a premature transition\n(out of 1000)")
    maximum_count = int(np.max(counts))
    y_max = max(10, int(np.ceil(1.15 * maximum_count / 10.0) * 10))
    ax_f.set_ylim(0, y_max)
    ax_f.yaxis.set_major_locator(MaxNLocator(nbins=6, integer=True))
    ax_f.set_title(r"$N=100, m=99, k_1=0.40, k_2=0.53$")
    ax_f.legend(frameon=False)
    ax_f.spines[['top','right']].set_visible(False)
    ax_f.bar_label(bars1, padding=3, fontsize=15)
    ax_f.bar_label(bars2, padding=3, fontsize=15)

    for ax, label in zip(axes.flat, "ABCDEF"):
        ax.text(-0.14, 1.06, label, transform=ax.transAxes, fontsize=30,
                fontweight='bold', va='bottom')
    plt.show()
    return fig, counts


if __name__ == "__main__":
    simulation_data = unfiltered_parameter_maps()
    theory_data = theory_parameter_maps(
        simulation_data[0], simulation_data[1], simulation_data[2]
    )
    confirmation_data = confirmation_parameter_map()
    bar_data = premature_counts()
    fig, counts = plot_panels(
        simulation_data, theory_data, confirmation_data, bar_data
    )
    print(counts)

# %% [notebook cell 9]
"""Compare simulation classifications at T=200 and T=1000.

For every valid (k1, k2) pair, one agent-level trajectory is observed at
both horizons. The entire sweep is repeated 10 times. The reported quantity
for each repeat is the percentage of parameter cells whose threshold-crossing
classification differs between T=200 and T=1000.
"""

from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
from numba import njit, prange

N = 100
R = 0.90
THRESHOLD = 0.99
HORIZON_SHORT = 200
HORIZON_LONG = 1000
REPEATS = 10
RESOLUTION = 101                 # parameter spacing 0.01
SEED = 20260906
# Works both as a .py script and in Colab/Jupyter cells.
OUT = Path.cwd()


def make_grid():
    values = np.linspace(0.0, 1.0, RESOLUTION)
    k1_grid, k2_grid = np.meshgrid(values, values)
    valid = ((k1_grid > 0) & (k2_grid > 0) &
             (k1_grid + k2_grid < 1))
    return k1_grid, k2_grid, valid


@njit(parallel=True, cache=True)
def run_sweeps(k1, k2):
    """Return crossing maps with shape (REPEATS, number of grid cells)."""
    n_points = k1.size
    complete_n = int(round(R * N))
    hit_200 = np.zeros((REPEATS, n_points), dtype=np.bool_)
    hit_1000 = np.zeros((REPEATS, n_points), dtype=np.bool_)

    # Parallelise over parameter cells. Updates within a round remain
    # sequential/in-place, as in the supplied Fig. D simulation.
    for p in prange(n_points):
        for repeat in range(REPEATS):
            np.random.seed(SEED + p * 1009 + repeat * 9176)
            belief = np.zeros(N)

            for t in range(1, HORIZON_LONG + 1):
                for i in range(N):
                    j = np.random.randint(0, N - 1)
                    if j >= i:
                        j += 1
                    if i < complete_n:
                        belief[i] = (k1[p] * belief[i]
                                     + k2[p] * belief[j]
                                     + 1.0 - k1[p] - k2[p])
                    else:
                        belief[i] = 0.0

                crossed = False
                for i in range(complete_n):
                    if belief[i] >= THRESHOLD:
                        crossed = True
                        break

                if crossed:
                    hit_1000[repeat, p] = True
                    if t <= HORIZON_SHORT:
                        hit_200[repeat, p] = True
                    break

    return hit_200, hit_1000


def plot_summary(k1, k2, hit_200, hit_1000):
    # For display only, a cell is positive if it crosses in any of 10 repeats.
    map_200 = np.any(hit_200, axis=0)
    map_1000 = np.any(hit_1000, axis=0)
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.8), constrained_layout=True)
    for ax, values, title in zip(
        axes, (map_200, map_1000), (r"$T=200$", r"$T=1000$")
    ):
        ax.scatter(k1[~values], k2[~values], s=11, marker="s",
                   c="#F2D93B", edgecolors="none", label="No crossing")
        ax.scatter(k1[values], k2[values], s=11, marker="s",
                   c="#D62728", edgecolors="none", label="Crossing")
        ax.set(xlabel=r"$k_1$", ylabel=r"$k_2$", title=title,
               xlim=(0, 1), ylim=(0, 1))
        ax.set_aspect("equal")
        ax.spines[["top", "right"]].set_visible(False)
    axes[1].legend(frameon=False, loc="upper right")
    fig.savefig(OUT / "T200_vs_T1000_simulation.png", dpi=300,
                bbox_inches="tight")


def main():
    k1_grid, k2_grid, valid = make_grid()
    k1, k2 = k1_grid[valid], k2_grid[valid]
    hit_200, hit_1000 = run_sweeps(k1, k2)

    disagreement = np.mean(hit_200 != hit_1000, axis=1) * 100.0
    changed_cells = np.sum(hit_200 != hit_1000, axis=1)
    print(f"Valid parameter cells: {k1.size}")
    for repeat, (count, percent) in enumerate(
            zip(changed_cells, disagreement), start=1):
        print(f"Repeat {repeat:2d}: {count:4d} cells, {percent:.4f}%")
    print(f"Mean disagreement: {disagreement.mean():.4f}%")
    print(f"SD across 10 repeats: {disagreement.std(ddof=1):.4f}%")

    np.savetxt(
        OUT / "T200_vs_T1000_disagreement.csv",
        np.column_stack((np.arange(1, REPEATS + 1), changed_cells,
                         disagreement)),
        delimiter=",", header="repeat,changed_cells,disagreement_percent",
        comments="", fmt=["%d", "%d", "%.8f"])
    np.savez_compressed(
        OUT / "T200_vs_T1000_data.npz", k1=k1, k2=k2,
        hit_200=hit_200, hit_1000=hit_1000)
    plot_summary(k1, k2, hit_200, hit_1000)


if __name__ == "__main__":
    main()

# %% [notebook cell 10]
"""Calculate the Fig. D theory-to-simulation F1 score at T=200.

Positive class: susceptibility to premature threshold crossing at r=0.9.
Prediction: moment-matched Beta theory. Ground truth: agent simulation.
Thus theory-only = false positive and simulation-only = false negative.
"""

from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
from numba import njit, prange
from scipy.stats import beta as beta_dist

N = 100
T = 200
R = 0.90
THRESHOLD = 0.99
TAU = 0.10
TRIALS = 10
RESOLUTION = 101
SEED = 20260906
# Works both as a .py script and in Colab/Jupyter cells.
OUT = Path.cwd()


def make_grid():
    x = np.linspace(0.0, 1.0, RESOLUTION)
    k1_grid, k2_grid = np.meshgrid(x, x)
    valid = ((k1_grid > 0) & (k2_grid > 0) &
             (k1_grid + k2_grid < 1))
    return k1_grid[valid], k2_grid[valid]


@njit(parallel=True, cache=True)
def simulation_map(k1, k2):
    """Positive if any robot crosses in any of 10 trials by T=200."""
    result = np.zeros(k1.size, dtype=np.bool_)
    complete_n = int(round(R * N))
    for p in prange(k1.size):
        for trial in range(TRIALS):
            np.random.seed(SEED + p * 1009 + trial * 9176)
            belief = np.zeros(N)
            for _t in range(T):
                for i in range(N):
                    j = np.random.randint(0, N - 1)
                    if j >= i:
                        j += 1
                    if i < complete_n:
                        belief[i] = (k1[p] * belief[i]
                                     + k2[p] * belief[j]
                                     + 1.0 - k1[p] - k2[p])
                    else:
                        belief[i] = 0.0
                for i in range(complete_n):
                    if belief[i] >= THRESHOLD:
                        result[p] = True
                        break
                if result[p]:
                    break
            if result[p]:
                break
    return result


def theory_map(k1, k2):
    """Moment-matched Beta classification used in Fig. D."""
    m = int(round(R * N))
    rho = (m - 1) / (N - 1)       # exact finite-population probability
    a = k1 + rho * k2
    b = 1.0 - k1 - k2
    c = k1**2 + rho * k2**2
    d = rho * (1.0 - rho) * k2**2
    mu = np.zeros_like(k1)
    variance = np.zeros_like(k1)
    predicted = np.zeros(k1.size, dtype=bool)

    for _t in range(T):
        variance, mu = c * variance + d * mu**2, a * mu + b
        quantile = mu.copy()
        stochastic = variance > np.finfo(float).eps
        ms, vs = mu[stochastic], variance[stochastic]
        nu = ms * (1.0 - ms) / vs - 1.0
        quantile[stochastic] = beta_dist.ppf(
            1.0 - TAU, ms * nu, (1.0 - ms) * nu)
        predicted |= quantile >= THRESHOLD
    return predicted


def main():
    k1, k2 = make_grid()
    truth = simulation_map(k1, k2)
    prediction = theory_map(k1, k2)

    tp = int(np.sum(prediction & truth))
    fp = int(np.sum(prediction & ~truth))
    fn = int(np.sum(~prediction & truth))
    tn = int(np.sum(~prediction & ~truth))
    precision = tp / (tp + fp) if tp + fp else float("nan")
    recall = tp / (tp + fn) if tp + fn else float("nan")
    f1 = 2 * tp / (2 * tp + fp + fn)
    print(f"TP={tp}, FP={fp}, FN={fn}, TN={tn}")
    print(f"Precision={precision:.6f}")
    print(f"Recall={recall:.6f}")
    print(f"F1={f1:.6f}")

    neither = ~prediction & ~truth
    both = prediction & truth
    theory_only = prediction & ~truth       # FP
    simulation_only = ~prediction & truth   # FN
    fig, ax = plt.subplots(figsize=(5.5, 5.2), constrained_layout=True)
    for mask, colour, label in (
        (neither, "#F2D93B", "Neither"),
        (both, "#D62728", "Both"),
        (theory_only, "#111111", "Theory only (FP)"),
        (simulation_only, "#1F77B4", "Simulation only (FN)"),
    ):
        ax.scatter(k1[mask], k2[mask], s=11, marker="s", c=colour,
                   edgecolors="none", label=label)
    ax.set(xlabel=r"$k_1$", ylabel=r"$k_2$", title=r"$T=200, r=0.9$",
           xlim=(0, 1), ylim=(0, 1))
    ax.set_aspect("equal")
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, fontsize=8)
    fig.savefig(OUT / "T200_theory_simulation_F1.png", dpi=300,
                bbox_inches="tight")


if __name__ == "__main__":
    main()

# %% [notebook cell 12]
# %matplotlib inline

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from scipy.stats import beta as beta_dist

plt.rcParams.update({
    'font.size': 18,
    'axes.labelsize': 20,
    'axes.titlesize': 18,
    'xtick.labelsize': 18,
    'ytick.labelsize': 18,
    'axes.grid': True,
    'grid.alpha': 0.3,
    'grid.linestyle': '--',
})

t_max = 100
r = 0.9
tail_value = 0.1
threshold_cutoff = 0.99

k1_vals = np.linspace(0, 1, 401)
k2_vals = np.linspace(0, 1, 401)
K1, K2 = np.meshgrid(k1_vals, k2_vals)

valid = (K1 + K2 < 1)

a = K1 + r * K2
b = 1 - K1 - K2
c = K1**2 + r * K2**2
d = r * (1 - r) * K2**2

# Mean and accumulated variance
X = np.zeros_like(K1)
V = np.zeros_like(K1)

for _ in range(t_max):
    X_next = a * X + b
    V_next = c * V + d * X**2
    X, V = X_next, V_next

# Final-time Beta quantile
threshold = np.full_like(X, np.nan)

# Zero variance: deterministic belief
point_mass = valid & (V == 0) & (X >= 0) & (X <= 1)
threshold[point_mass] = X[point_mass]

# Valid moment-matched Beta distribution
beta_ok = (
    valid
    & (X > 0)
    & (X < 1)
    & (V > 0)
    & (V < X * (1 - X))
)

s = X[beta_ok] * (1 - X[beta_ok]) / V[beta_ok] - 1
alpha = X[beta_ok] * s
beta_param = (1 - X[beta_ok]) * s

threshold[beta_ok] = beta_dist.ppf(
    1 - tail_value, alpha, beta_param
)

# Classification
Class = np.full_like(X, np.nan)
Class[valid & (threshold < threshold_cutoff)] = 0
Class[valid & (threshold >= threshold_cutoff)] = 1

# One figure only
plt.figure(figsize=(10, 10))

im = plt.imshow(
    Class,
    origin='lower',
    extent=[0, 1, 0, 1],
    cmap=ListedColormap(['yellow', 'red']),
    vmin=0,
    vmax=1,
    aspect='equal'
)

plt.plot([0, 1], [1, 0], 'k', linewidth=2)
plt.xlabel(r'$k_1$')
plt.ylabel(r'$k_2$')
plt.title(r'Accumulated Variance Heatmap at $t=100$')

cbar = plt.colorbar(im, ticks=[0, 1], shrink=0.5)
cbar.ax.set_yticklabels([
    'Final-time quantile < 0.99',
    'Final-time quantile ≥ 0.99'
])

plt.tight_layout()
plt.show()

# %% [notebook cell 13]
# %matplotlib inline

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from scipy.stats import beta as beta_dist

# Optional acceleration; the simulation rule remains unchanged.
try:
    from numba import njit
    print("Numba acceleration enabled.")
except ImportError:
    def njit(func):
        return func
    print("Numba unavailable: using Python, which will be slower.")


# -----------------------------
# Simulation function
# Sequential, in-place updates
# -----------------------------
@njit
def run_simulation(
    k1,
    k2,
    r,
    num_agents=100,
    num_rounds=200,
    threshold_cutoff=0.99,
    seed=0
):
    np.random.seed(seed)

    # Round instead of truncate:
    # int(100 * (1 - 0.9)) can incorrectly give 9.
    n_unfinished = int(round(num_agents * (1 - r)))
    n_unfinished = min(num_agents, max(0, n_unfinished))

    # Random completion times: 1 to 10
    completion_rounds = np.random.randint(
        1, 11, size=num_agents
    )

    # Avoid [-0:] selecting every agent
    if n_unfinished > 0:
        completion_rounds[-n_unfinished:] = num_rounds + 1

    P_all = np.zeros(num_agents)

    for t in range(num_rounds):
        states = (t >= completion_rounds)

        # Preserve your original sequential update order
        for i in range(num_agents):

            # Random neighbour, excluding self
            j = np.random.randint(0, num_agents - 1)
            if j >= i:
                j += 1

            if not states[i]:
                P_all[i] = 0.0
            else:
                P_all[i] = (
                    k1 * P_all[i]
                    + k2 * P_all[j]
                    + (1 - k1 - k2)
                )

        # Record ANY premature detection during the run.
        # Early return is sufficient for this binary event.
        if (
            np.any(P_all >= threshold_cutoff)
            and not np.all(states)
        ):
            return True

    return False


# -----------------------------
# Parameters
# -----------------------------
r = 0.9
t_max = 200
num_agents = 100
n_repeat = 10

tail_value = 0.1
threshold_cutoff = 0.99

k1_vals = np.linspace(0, 1, 101)
k2_vals = np.linspace(0, 1, 101)

K1, K2 = np.meshgrid(k1_vals, k2_vals)

# Integer grid indices avoid floating-point errors
# at the mathematical boundary k1 + k2 = 1.
row, col = np.indices(K1.shape)
valid = (row + col < len(k1_vals) - 1)

# Reproducible Monte Carlo seeds
rng = np.random.default_rng(20260830)


# -----------------------------
# Simulation classification
# -----------------------------
Class_sim = np.full_like(K1, np.nan)
Error_rate = np.full_like(K1, np.nan)

total_points = int(np.sum(valid))
completed_points = 0

print(f"Simulation started: {total_points} parameter pairs.")
print(f"{n_repeat} repetitions per pair, {t_max} rounds per run.")

for i, k1 in enumerate(k1_vals):
    for j, k2 in enumerate(k2_vals):

        if not valid[j, i]:
            continue

        count = 0

        for repeat in range(n_repeat):
            trial_seed = int(rng.integers(0, 2**31 - 1))

            hit = run_simulation(
                k1,
                k2,
                r,
                num_agents=num_agents,
                num_rounds=t_max,
                threshold_cutoff=threshold_cutoff,
                seed=trial_seed
            )

            if hit:
                count += 1

        error_rate = count / n_repeat

        Error_rate[j, i] = error_rate
        Class_sim[j, i] = 1 if count > 0 else 0

        completed_points += 1

    if i % 10 == 0 or i == len(k1_vals) - 1:
        print(
            f"Progress: {completed_points}/{total_points} "
            f"({100 * completed_points / total_points:.1f}%)",
            flush=True
        )


# -----------------------------
# Theoretical model
# Accumulated mean and variance
# -----------------------------
a = K1 + r * K2
b = 1 - K1 - K2
c = K1**2 + r * K2**2
d = r * (1 - r) * K2**2

X = np.zeros_like(K1)
V = np.zeros_like(K1)

for _ in range(t_max):
    # Both right-hand sides use previous-round moments
    X_next = a * X + b
    V_next = c * V + d * X**2

    X = X_next
    V = V_next


# -----------------------------
# Final-time Beta quantile
# -----------------------------
threshold = np.full_like(X, np.nan)

# Zero variance: deterministic point mass
point_mass = (
    valid
    & (V == 0)
    & (X >= 0)
    & (X <= 1)
)
threshold[point_mass] = X[point_mass]

# Admissible moment-matched Beta distribution
beta_ok = (
    valid
    & (X > 0)
    & (X < 1)
    & (V > 0)
    & (V < X * (1 - X))
)

concentration = (
    X[beta_ok] * (1 - X[beta_ok]) / V[beta_ok] - 1
)

alpha = X[beta_ok] * concentration
beta_param = (1 - X[beta_ok]) * concentration

threshold[beta_ok] = beta_dist.ppf(
    1 - tail_value,
    alpha,
    beta_param
)


# -----------------------------
# Theory classification
# -----------------------------
Class_theory = np.full_like(X, np.nan)

Class_theory[
    valid & (threshold >= threshold_cutoff)
] = 1

Class_theory[
    valid & (threshold < threshold_cutoff)
] = 0


# -----------------------------
# Comparison map: four classes
# -----------------------------
Comparison = np.full_like(Class_sim, np.nan)

# 0: neither method classifies as hit
Comparison[
    valid & (Class_sim == 0) & (Class_theory == 0)
] = 0

# 1: both classify as hit
Comparison[
    valid & (Class_sim == 1) & (Class_theory == 1)
] = 1

# 2: theory predicts hit, simulation observes none
Comparison[
    valid & (Class_sim == 0) & (Class_theory == 1)
] = 2

# 3: simulation observes hit, theory does not predict it
Comparison[
    valid & (Class_sim == 1) & (Class_theory == 0)
] = 3

undefined = int(np.sum(valid & np.isnan(Comparison)))
if undefined:
    print(f"Warning: {undefined} valid points could not be classified.")


# -----------------------------
# Plot: one figure, no saving
# -----------------------------
plt.rcParams.update({
    'font.size': 16,
    'axes.labelsize': 20,
    'axes.titlesize': 18,
    'xtick.labelsize': 16,
    'ytick.labelsize': 16,
})

fig, ax = plt.subplots(figsize=(10, 10))

cmap = ListedColormap([
    'yellow',
    'red',
    'deepskyblue',
    'black'
])

im = ax.imshow(
    Comparison,
    origin='lower',
    extent=[0, 1, 0, 1],
    cmap=cmap,
    vmin=0,
    vmax=3,
    aspect='equal'
)

ax.plot([0, 1], [1, 0], 'k', linewidth=1)

ax.set_title(
    f'Accumulated-variance theory vs simulation\n'
    f'r = {r}, t = {t_max}'
)
ax.set_xlabel(r'$k_1$')
ax.set_ylabel(r'$k_2$')

cbar = fig.colorbar(
    im,
    ax=ax,
    ticks=[0, 1, 2, 3],
    shrink=0.5
)

cbar.set_ticklabels([
    'No-hit agreement',
    'Hit agreement',
    'Theory only',
    'Simulation only'
])

plt.tight_layout()
plt.show()

# %% [notebook cell 15]
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

    'font.size': 22,
    'axes.labelsize': 22,
    'axes.titlesize': 22,
    'xtick.labelsize': 22,
    'ytick.labelsize': 22,
    'legend.fontsize': 22,

    'lines.linewidth': 1.5,
    'lines.markersize': 6,

    'axes.grid': False,
    'axes.linewidth': 1.2,
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

# Parameter grid: 0.00, 0.01, ..., 1.00.
K_RESOLUTION = 101

# One spatial realisation per parameter map.
# Increase for a repeated-run analysis.
N_REPEATS = 10

# With multiple repetitions:
# red means at least one repetition contains a threshold crossing.
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
valid = (K1 + K2 < 1.0 - 1e-12)

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
# A parameter point is red as soon as any agent reaches 0.99.
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
):
    n_points = len(k1_array)
    n_rounds = len(pair_counts)

    # -1 means no threshold crossing.
    first_hit_round = np.full(
        n_points,
        -1,
        dtype=np.int32,
    )

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

        # Explicitly keep unfinished agents at zero.
        for i in range(
            completed_agents,
            n_agents,
        ):
            beliefs[i] = 0.0

        # General initial-state check.
        initial_hit = False

        for i in range(n_agents):
            if beliefs[i] >= threshold:
                initial_hit = True
                break

        if initial_hit:
            first_hit_round[parameter_index] = 0
            continue

        hit = False

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

                # Any threshold crossing at any round is a hit.
                if (
                    new_i >= threshold
                    or
                    new_j >= threshold
                ):
                    first_hit_round[
                        parameter_index
                    ] = round_index + 1

                    hit = True
                    break

            if hit:
                break

    return first_hit_round


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
    "The first call also compiles the Numba functions."
)

all_hit_maps = []
all_event_frequencies = []

for range_index, comm_range in enumerate(COMM_RANGES):

    event_counts = np.zeros(
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

        print(
            "  Evaluating parameter grid..."
        )

        first_hit_round = evaluate_parameter_grid(
            k1_points,
            k2_points,
            pairs,
            pair_counts,
            TOTAL_AGENTS,
            COMPLETED_AGENTS,
            INITIAL_BELIEF,
            BELIEF_THRESHOLD,
        )

        event_counts += (
            first_hit_round >= 0
        )

        del pairs
        del pair_counts
        del first_hit_round

    # Red if any tested repetition contains a hit.
    hit_map = (event_counts > 0)

    all_hit_maps.append(hit_map)

    all_event_frequencies.append(
        event_counts / N_REPEATS
    )

    print(
        f"  Red parameter points: "
        f"{np.count_nonzero(hit_map)}"
    )

    print(
        f"  Yellow parameter points: "
        f"{np.count_nonzero(~hit_map)}"
    )

# ============================================================
# 7. Plot three heatmaps
# ============================================================
YELLOW = '#F2D93B'
RED = '#D62728'

cmap = ListedColormap([
    YELLOW,
    RED,
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
    figsize=(24, 9),
)

fig.subplots_adjust(
    left=0.06,
    right=0.98,
    bottom=0.20,
    top=0.90,
    wspace=0.25,
)

dx = k1_values[1] - k1_values[0]
dy = k2_values[1] - k2_values[0]

for panel_index, (
    ax,
    comm_range,
    hit_map,
) in enumerate(
    zip(
        axes,
        COMM_RANGES,
        all_hit_maps,
    )
):
    heatmap = np.full(
        K1.shape,
        np.nan,
    )

    heatmap[valid] = hit_map.astype(float)

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
        linewidth=1.8,
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
        f'Communication range: '
        f'{comm_range:g} px',
        pad=16,
    )

    ax.grid(False, which='both')

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    # Panel labels A, B, C.
    ax.text(
        -0.13,
        1.06,
        chr(ord('A') + panel_index),
        transform=ax.transAxes,
        fontsize=26,
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
        markerfacecolor=YELLOW,
        markeredgecolor='none',
        markersize=12,
        label='No premature event observed',
    ),
    Line2D(
        [],
        [],
        marker='s',
        linestyle='none',
        markerfacecolor=RED,
        markeredgecolor='none',
        markersize=12,
        label='Premature event observed at least once',
    ),
]

fig.legend(
    handles=legend_handles,
    loc='lower center',
    bbox_to_anchor=(0.5, 0.06),
    ncol=2,
    frameon=False,
    fontsize=16,
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

for comm_range, hit_map in zip(
    COMM_RANGES,
    all_hit_maps,
):
    print(
        f"Range {comm_range:g} px: "
        f"red={np.count_nonzero(hit_map)}, "
        f"yellow={np.count_nonzero(~hit_map)}"
    )

# %% [notebook cell 17]
import numpy as np
import matplotlib.pyplot as plt
import json
from collections import deque

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
LMC_CONFIRMATION_ROUNDS = 5


# =========================================================
# OUTPUT FILES
# =========================================================
RUN_SIMULATION = True

OUTPUT_DATA = "lmc_battery_simulation_results.npz"

OUTPUT_PNG = (
    "science_robotics_battery_"
    "method_comparison_no_dropout_1x3.png"
)

OUTPUT_PDF = (
    "science_robotics_battery_"
    "method_comparison_no_dropout_1x3.pdf"
)


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

    "Battery threshold",

    "Centralised controller",

    "Full-state flooding",

    "Anonymous Protocol",

    "Identity-Aware Protocol with Message Re-broadcasting (ID+R)",

    "Linear Meta-Completion (LMC)",
]


METHODS_DROPOUT = [

    "Battery threshold",

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

    "Battery threshold": {

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
    rows,
    columns,
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


    deliveries = []


    # -----------------------------------------------------
    # Every active robot broadcasts ENTIRE table
    # to ALL active orthogonal neighbours.
    # -----------------------------------------------------
    for sender in np.flatnonzero(
        active_mask
    ):

        neighbors = (
            orthogonal_neighbors(

                int(sender),

                rows,

                columns,

                active_mask,
            )
        )


        for receiver in neighbors:

            deliveries.append(

                (
                    int(
                        receiver
                    ),

                    snapshots[
                        int(sender)
                    ],
                )
            )


    # -----------------------------------------------------
    # Merge received tables.
    # -----------------------------------------------------
    for (
        receiver,
        sender_table,
    ) in deliveries:

        flooding_merge_table(

            tables[
                receiver
            ],

            sender_table,
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
            "Battery threshold"
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
        flooding_communication_round(

            flooding_tables,

            active_mask,

            rows,

            columns,
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
        # 6. LINEAR META-Completion (LMC)
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
    method_names = saved["method_names"].tolist()
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
                method_name,

            linewidth=
                2.6,

            markersize=
                7.0,

            markeredgewidth=
                1.0,

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
            "Mean active agents "
            "transitioned (%)"
        )


    else:

        completion_label = (

            "True global "
            "completion range "
            f"("
            f"{completion_min:.0f}"
            f"–"
            f"{completion_max:.0f}"
            f")"
        )


        ylabel = (
            "Mean agents "
            "transitioned (%)"
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
            22,

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
                14,

            ha=
                "right",

            va=
                "bottom",
        )


    # A single shared legend is added after all four panels
    # have been drawn.


# =========================================================
# MAIN
# =========================================================
def main():

    print(
        "="
        *
        70
    )


    print(
        "BATTERY / META-COMPLETION CONFIGURATION"
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
    if RUN_SIMULATION:

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
            16,

        "axes.labelsize":
            18,

        "axes.titlesize":
            18,

        "xtick.labelsize":
            15,

        "ytick.labelsize":
            15,

        "legend.fontsize":
            14,

        "axes.linewidth":
            1.4,

        "xtick.major.width":
            1.2,

        "ytick.major.width":
            1.2,

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
            (21.0, 7.5),

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

        loc=
            "lower center",

        bbox_to_anchor=
            (0.50, 0.015),

        ncol=
            3,

        frameon=
            False,

        fontsize=
            14,

        handlelength=
            2.5,

        handletextpad=
            0.6,

        labelspacing=
            0.65,
    )


    fig.subplots_adjust(

        left=
            0.055,

        right=
            0.985,

        bottom=
            0.34,

        top=
            0.96,

        wspace=
            0.25,
    )


    # =====================================================
    # SAVE
    # =====================================================
    fig.savefig(

        OUTPUT_PDF,

        bbox_inches=
            "tight",

        pad_inches=
            0.04,
    )


    fig.savefig(

        OUTPUT_PNG,

        dpi=
            600,

        bbox_inches=
            "tight",

        pad_inches=
            0.04,
    )


    print(

        f"Saved "
        f"{OUTPUT_PDF}"
    )


    print(

        f"Saved "
        f"{OUTPUT_PNG}"
    )


    plt.show()


# =========================================================
# RUN
# =========================================================
if __name__ == "__main__":

    main()

# %% [notebook cell 18]
import numpy as np
import matplotlib.pyplot as plt
import json
import csv
from collections import deque

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
LMC_CONFIRMATION_ROUNDS = 5


# =========================================================
# OUTPUT FILES
# =========================================================
RUN_SIMULATION = True

OUTPUT_DATA = "lmc_battery_simulation_results.npz"

OUTPUT_PNG = (
    "science_robotics_battery_"
    "method_comparison_no_dropout_1x3.png"
)

OUTPUT_PDF = (
    "science_robotics_battery_"
    "method_comparison_no_dropout_1x3.pdf"
)

PREMATURE_TRIAL_CSV = "method_comparison_trial_events.csv"
PREMATURE_SUMMARY_CSV = "method_comparison_premature_counts.csv"
PREMATURE_OUTPUT_PNG = "method_comparison_premature_counts.png"
PREMATURE_OUTPUT_PDF = "method_comparison_premature_counts.pdf"


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

    "Battery threshold",

    "Centralised controller",

    "Full-state flooding",

    "Anonymous Protocol",

    "Identity-Aware Protocol with Message Re-broadcasting (ID+R)",

    "Linear Meta-Completion (LMC)",
]


METHODS_DROPOUT = [

    "Battery threshold",

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

    "Battery threshold": {

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
    rows,
    columns,
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


    deliveries = []


    # -----------------------------------------------------
    # Every active robot broadcasts ENTIRE table
    # to ALL active orthogonal neighbours.
    # -----------------------------------------------------
    for sender in np.flatnonzero(
        active_mask
    ):

        neighbors = (
            orthogonal_neighbors(

                int(sender),

                rows,

                columns,

                active_mask,
            )
        )


        for receiver in neighbors:

            deliveries.append(

                (
                    int(
                        receiver
                    ),

                    snapshots[
                        int(sender)
                    ],
                )
            )


    # -----------------------------------------------------
    # Merge received tables.
    # -----------------------------------------------------
    for (
        receiver,
        sender_table,
    ) in deliveries:

        flooding_merge_table(

            tables[
                receiver
            ],

            sender_table,
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
            "Battery threshold"
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
        flooding_communication_round(

            flooding_tables,

            active_mask,

            rows,

            columns,
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
        # 6. LINEAR META-Completion (LMC)
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
    method_names = saved["method_names"].tolist()
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
                method_name,

            linewidth=
                2.6,

            markersize=
                7.0,

            markeredgewidth=
                1.0,

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
            "Mean active agents "
            "transitioned (%)"
        )


    else:

        completion_label = (

            "True global "
            "completion range "
            f"("
            f"{completion_min:.0f}"
            f"–"
            f"{completion_max:.0f}"
            f")"
        )


        ylabel = (
            "Mean agents "
            "transitioned (%)"
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
            22,

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
                14,

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
        "Battery threshold": "Local\nthreshold",
        "Centralised controller": "Centralised\nreference",
        "Fixed-membership centralised controller": "Centralised\nreference",
        "Full-state flooding": "Full-state\nFlooding",
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
        figsize=(18.4 / 2.54, 6.3 / 2.54),
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
            linewidth=0.5,
        )
        ax.bar_label(
            bars,
            labels=[f"{count}/{total}" for count, total in zip(counts, totals)],
            padding=2,
            fontsize=7,
        )
        ax.set_xticks(x)
        ax.set_xticklabels(
            [short_names.get(method, method) for method in methods],
            rotation=35,
            ha="right",
            fontsize=7,
        )
        ax.tick_params(axis="y", labelsize=8)
        max_runs = int(np.max(totals))
        ax.set_ylim(0, max_runs + 1)
        ax.set_yticks(np.arange(0, max_runs + 1, 2))
        ax.grid(axis="y", color="#D9D9D9", linewidth=0.5)
        ax.set_axisbelow(True)
        num_agents = int(
            experiment["config"]["rows"]
            * experiment["config"]["columns"]
        )
        ax.set_title(
            f"{panel}   N = {num_agents}",
            loc="left",
            fontweight="bold",
            fontsize=9,
        )
        if panel_index == 0:
            ax.set_ylabel(
                "Runs with a premature transition",
                fontsize=8,
            )

    fig.tight_layout(w_pad=1.0)
    fig.savefig(
        PREMATURE_OUTPUT_PNG,
        dpi=600,
        bbox_inches="tight",
    )
    fig.savefig(
        PREMATURE_OUTPUT_PDF,
        bbox_inches="tight",
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

    print(
        "="
        *
        70
    )


    print(
        "BATTERY / META-COMPLETION CONFIGURATION"
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
    if RUN_SIMULATION:

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
            16,

        "axes.labelsize":
            18,

        "axes.titlesize":
            18,

        "xtick.labelsize":
            15,

        "ytick.labelsize":
            15,

        "legend.fontsize":
            14,

        "axes.linewidth":
            1.4,

        "xtick.major.width":
            1.2,

        "ytick.major.width":
            1.2,

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
            (21.0, 7.5),

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

        loc=
            "lower center",

        bbox_to_anchor=
            (0.50, 0.015),

        ncol=
            3,

        frameon=
            False,

        fontsize=
            14,

        handlelength=
            2.5,

        handletextpad=
            0.6,

        labelspacing=
            0.65,
    )


    fig.subplots_adjust(

        left=
            0.055,

        right=
            0.985,

        bottom=
            0.34,

        top=
            0.96,

        wspace=
            0.25,
    )


    # =====================================================
    # SAVE
    # =====================================================
    fig.savefig(

        OUTPUT_PDF,

        bbox_inches=
            "tight",

        pad_inches=
            0.04,
    )


    fig.savefig(

        OUTPUT_PNG,

        dpi=
            600,

        bbox_inches=
            "tight",

        pad_inches=
            0.04,
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

# %% [notebook cell 19]
import numpy as np
import matplotlib.pyplot as plt
import json

INPUT_DATA = "lmc_battery_simulation_results.npz"

OUTPUT_PNG = "supp_premature_counts.png"
OUTPUT_PDF = "supp_premature_counts.pdf"

SHORT_NAMES = {
    "Battery threshold": "Local",
    "Centralised controller": "Centralised",
    "Fixed-membership centralised controller": "Centralised",
    "Full-state flooding": "Flooding",
    "Anonymous Protocol": "Anonymous",
    "Identity-Aware Protocol with Message Re-broadcasting (ID+R)": "ID+R",
    "Linear Meta-Completion (LMC)": "LMC",
}

METHOD_COLORS = {
    "Battery threshold": "#ff7f0e",
    "Centralised controller": "#9467bd",
    "Fixed-membership centralised controller": "#9467bd",
    "Full-state flooding": "#2ca02c",
    "Anonymous Protocol": "#d62728",
    "Identity-Aware Protocol with Message Re-broadcasting (ID+R)": "#8c564b",
    "Linear Meta-Completion (LMC)": "#111111",
}

# ============================================================
# Load saved simulation results
# ============================================================

saved = np.load(INPUT_DATA, allow_pickle=False)

method_names = saved["method_names"].tolist()
panel_labels = saved["panel_labels"].tolist()
method_present = saved["method_present"]
repetition_curves = saved["repetition_curves"]
completion_rounds = saved["completion_rounds"]
configs = json.loads(str(saved["configs_json"]))

summary_rows = []

for panel_index, panel in enumerate(panel_labels):

    valid_completion_rounds = completion_rounds[panel_index]
    valid_runs = np.flatnonzero(valid_completion_rounds >= 0)

    for method_index, method in enumerate(method_names):

        if not method_present[panel_index, method_index]:
            continue

        premature_count = 0

        for repetition_index in valid_runs:

            true_completion = int(
                valid_completion_rounds[repetition_index]
            )

            curve = np.asarray(
                repetition_curves[
                    panel_index,
                    repetition_index,
                    method_index
                ],
                dtype=float
            )

            if np.all(np.isnan(curve)):
                continue

            first = np.flatnonzero(curve > 1e-12)

            first_transition = (
                int(first[0])
                if first.size > 0
                else None
            )

            if (
                first_transition is not None
                and first_transition < true_completion
            ):
                premature_count += 1

        summary_rows.append({
            "Panel": panel,
            "Method": method,
            "Premature": premature_count,
            "Total": len(valid_runs),
        })

# ============================================================
# Plot style
# ============================================================

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "font.size": 11,
    "axes.labelsize": 13,
    "axes.titlesize": 14,
    "xtick.labelsize": 10.5,
    "ytick.labelsize": 11,
    "axes.linewidth": 1.0,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
})

fig, axes = plt.subplots(
    1,
    3,
    figsize=(12, 4.2),
    sharey=True,
)

panel_titles = {
    "A": r"$\mathbf{A}$  $N=100$",
    "B": r"$\mathbf{B}$  $N=1000$",
    "C": r"$\mathbf{C}$  $N=100$, heterogeneous",
}

for ax, panel in zip(axes, panel_labels):

    rows = [
        row for row in summary_rows
        if row["Panel"] == panel
    ]

    methods = [row["Method"] for row in rows]
    counts = np.array([row["Premature"] for row in rows])
    totals = np.array([row["Total"] for row in rows])

    x = np.arange(len(methods))

    bars = ax.bar(
        x,
        counts,
        width=0.64,
        color=[METHOD_COLORS[m] for m in methods],
        edgecolor="black",
        linewidth=0.6,
    )

    for bar, count, total in zip(bars, counts, totals):

        y = count + 0.15 if count > 0 else 0.12

        ax.text(
            bar.get_x() + bar.get_width() / 2,
            y,
            f"{count}/{total}",
            ha="center",
            va="bottom",
            fontsize=10,
        )

    ax.set_xticks(x)
    ax.set_xticklabels(
        [SHORT_NAMES[m] for m in methods],
        rotation=30,
        ha="right",
    )

    ax.set_ylim(0, 11.3)
    ax.set_yticks(np.arange(0, 11, 2))

    ax.set_title(
        panel_titles[panel],
        loc="left",
        pad=8,
    )

    ax.grid(
        axis="y",
        alpha=0.25,
        linewidth=0.6,
    )

    ax.set_axisbelow(True)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

axes[0].set_ylabel(
    "Runs with a premature transition"
)

fig.subplots_adjust(
    left=0.08,
    right=0.99,
    bottom=0.23,
    top=0.88,
    wspace=0.20,
)

fig.savefig(
    OUTPUT_PNG,
    dpi=600,
    bbox_inches="tight",
)

fig.savefig(
    OUTPUT_PDF,
    bbox_inches="tight",
)

plt.show()

# %% [notebook cell 20]
import numpy as np
import matplotlib.pyplot as plt

# ============================================================
# SETTINGS
# ============================================================

ROWS = 10
COLUMNS = 10
N = ROWS * COLUMNS

# Run longer than the original 700-round experiment
NUM_ROUNDS = 1200
ORIGINAL_HORIZON = 700

BATTERY_THRESHOLD = 100.0

NORMAL_CHARGE = 2.0
SLOW_CHARGE = 0.5
NUM_SLOW = 10

# Same seeds as the first repetition of panel C
BATTERY_SEED = 12
COMMUNICATION_SEED = 1200

# Final Figure 5 LMC parameters
K1 = 0.40
K2 = 0.57

THETA = 0.99
CONFIRMATION_ROUNDS = 5

OUTPUT_PNG = "heterogeneous_LMC_belief_evolution.png"
OUTPUT_PDF = "heterogeneous_LMC_belief_evolution.pdf"


# ============================================================
# ORTHOGONAL GRID
# ============================================================

def orthogonal_neighbors(agent_id):
    row = agent_id // COLUMNS
    col = agent_id % COLUMNS

    neighbors = []

    if row > 0:
        neighbors.append(agent_id - COLUMNS)

    if row < ROWS - 1:
        neighbors.append(agent_id + COLUMNS)

    if col > 0:
        neighbors.append(agent_id - 1)

    if col < COLUMNS - 1:
        neighbors.append(agent_id + 1)

    return neighbors


def random_orthogonal_neighbor(agent_id, rng):
    candidates = orthogonal_neighbors(agent_id)

    if not candidates:
        return None

    return int(rng.choice(candidates))


# ============================================================
# BATTERY INITIALISATION
# Matches your Panel C code
# ============================================================

battery_rng = np.random.Generator(
    np.random.PCG64(BATTERY_SEED)
)

initial_battery = battery_rng.integers(
    0,
    int(BATTERY_THRESHOLD) + 1,
    size=N,
    dtype=np.int16,
).astype(float)


charge_rates = np.full(
    N,
    NORMAL_CHARGE,
    dtype=float,
)


# IMPORTANT:
# This is the same separate RNG used in your original code
# for selecting slow robots.
slow_rng = np.random.default_rng(
    BATTERY_SEED + 900000
)

slow_ids = np.sort(
    slow_rng.choice(
        N,
        size=NUM_SLOW,
        replace=False,
    )
)

charge_rates[slow_ids] = SLOW_CHARGE


print("Slow robots:")
print(slow_ids.tolist())


# ============================================================
# BATTERY HISTORY
# ============================================================

rounds = np.arange(
    NUM_ROUNDS + 1,
    dtype=float,
)

battery_history = np.minimum(
    initial_battery[:, None]
    +
    charge_rates[:, None] * rounds[None, :],
    BATTERY_THRESHOLD,
)

completion_history = (
    battery_history >= BATTERY_THRESHOLD
).astype(np.uint8)


# ============================================================
# TRUE COMPLETION TIMES
# ============================================================

individual_completion_rounds = np.argmax(
    completion_history == 1,
    axis=1,
)

true_completion_round = int(
    np.max(individual_completion_rounds)
)

first_local_completion_round = int(
    np.min(individual_completion_rounds)
)


print()
print("First local completion round:",
      first_local_completion_round)

print("True global completion round:",
      true_completion_round)


# ============================================================
# LMC
# ============================================================

rng_lmc = np.random.default_rng(
    COMMUNICATION_SEED + 200000
)

belief = np.zeros(
    N,
    dtype=float,
)

belief_history = np.zeros(
    (N, NUM_ROUNDS + 1),
    dtype=float,
)

confirmation = np.zeros(
    N,
    dtype=np.int16,
)

transitioned = np.zeros(
    N,
    dtype=bool,
)

transition_round = np.full(
    N,
    -1,
    dtype=int,
)


# ============================================================
# SIMULATION
# ============================================================

for t in range(
    1,
    NUM_ROUNDS + 1,
):

    current_states = completion_history[:, t]

    # Synchronous LMC:
    # every receiver reads beliefs from previous round.
    previous_belief = belief.copy()

    for i in range(N):

        # ---------------------------------------------
        # unfinished robot -> belief = 0
        # ---------------------------------------------
        if current_states[i] == 0:
            belief[i] = 0.0
            continue

        # ---------------------------------------------
        # random orthogonal neighbour
        # ---------------------------------------------
        j = random_orthogonal_neighbor(
            i,
            rng_lmc,
        )

        if j is None:
            belief[i] = 0.0
            continue

        belief[i] = (
            K1 * previous_belief[i]
            +
            K2 * previous_belief[j]
            +
            (1.0 - K1 - K2)
        )

        # Numerical safeguard only
        belief[i] = np.clip(
            belief[i],
            0.0,
            1.0,
        )


    # ========================================================
    # FIVE-ROUND CONFIRMATION
    # ========================================================

    above = (
        belief >= THETA
    )

    confirmation = np.where(
        above,
        confirmation + 1,
        0,
    )

    newly_transitioned = (
        (~transitioned)
        &
        (
            confirmation
            >=
            CONFIRMATION_ROUNDS
        )
    )

    transition_round[
        newly_transitioned
    ] = t

    transitioned |= newly_transitioned


    belief_history[:, t] = belief


# ============================================================
# DIAGNOSTICS
# ============================================================

valid_transition_rounds = transition_round[
    transition_round >= 0
]

if valid_transition_rounds.size > 0:
    first_lmc_transition = int(
        np.min(valid_transition_rounds)
    )
else:
    first_lmc_transition = None


if np.all(
    transition_round >= 0
):
    all_lmc_transition = int(
        np.max(transition_round)
    )
else:
    all_lmc_transition = None


transitioned_by_700 = (
    (transition_round >= 0)
    &
    (transition_round <= ORIGINAL_HORIZON)
)

transitioned_by_end = (
    transition_round >= 0
)


print()
print("=" * 70)
print("HETEROGENEOUS LMC DIAGNOSTICS")
print("=" * 70)

print(
    f"N = {N}"
)

print(
    f"k1 = {K1}, k2 = {K2}"
)

print(
    f"Slow robots = {NUM_SLOW}"
)

print(
    f"True global completion = round "
    f"{true_completion_round}"
)

print(
    f"First LMC transition = "
    f"{first_lmc_transition}"
)

print(
    f"Final LMC transition = "
    f"{all_lmc_transition}"
)

print(
    f"Robots transitioned by round 700 = "
    f"{np.sum(transitioned_by_700)}/{N}"
)

print(
    f"Robots NOT transitioned by round 700 = "
    f"{N - np.sum(transitioned_by_700)}"
)

print(
    f"Robots transitioned by round {NUM_ROUNDS} = "
    f"{np.sum(transitioned_by_end)}/{N}"
)

if all_lmc_transition is not None:

    print(
        "Final detection delay after global completion = "
        f"{all_lmc_transition - true_completion_round} rounds"
    )

else:

    print(
        f"Not all robots transitioned by round "
        f"{NUM_ROUNDS}."
    )


# ============================================================
# BELIEF STATISTICS
# ============================================================

mean_belief = np.mean(
    belief_history,
    axis=0,
)

min_belief = np.min(
    belief_history,
    axis=0,
)

max_belief = np.max(
    belief_history,
    axis=0,
)


# ============================================================
# PLOT
# ============================================================

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": [
        "Arial",
        "Helvetica",
        "DejaVu Sans",
    ],
    "font.size": 12,
    "axes.labelsize": 15,
    "axes.titlesize": 16,
    "xtick.labelsize": 12,
    "ytick.labelsize": 12,
    "axes.linewidth": 1.1,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
})


fig, ax = plt.subplots(
    figsize=(12.5, 6.3)
)


normal_ids = np.setdiff1d(
    np.arange(N),
    slow_ids,
)


# ------------------------------------------------------------
# NORMAL ROBOTS
# ------------------------------------------------------------

for i in normal_ids:

    ax.plot(
        np.arange(NUM_ROUNDS + 1),
        belief_history[i],
        linewidth=0.7,
        alpha=0.20,
    )


# ------------------------------------------------------------
# SLOW ROBOTS
# ------------------------------------------------------------

for i in slow_ids:

    ax.plot(
        np.arange(NUM_ROUNDS + 1),
        belief_history[i],
        linewidth=1.15,
        alpha=0.70,
        linestyle="--",
    )


# ------------------------------------------------------------
# MEAN BELIEF
# ------------------------------------------------------------

ax.plot(
    np.arange(NUM_ROUNDS + 1),
    mean_belief,
    linewidth=2.5,
    label="Mean belief",
)


# ------------------------------------------------------------
# DETECTION THRESHOLD
# ------------------------------------------------------------

ax.axhline(
    THETA,
    linestyle="--",
    linewidth=1.5,
    label=r"Detection threshold $\theta=0.99$",
)


# ------------------------------------------------------------
# TRUE GLOBAL COMPLETION
# ------------------------------------------------------------

ax.axvline(
    true_completion_round,
    linestyle="--",
    linewidth=1.6,
    label=(
        "True global completion "
        f"(round {true_completion_round})"
    ),
)


# ------------------------------------------------------------
# ORIGINAL 700-ROUND HORIZON
# ------------------------------------------------------------

ax.axvline(
    ORIGINAL_HORIZON,
    linestyle=":",
    linewidth=1.4,
    label="Original observation horizon (700)",
)


# ------------------------------------------------------------
# FIRST / FINAL TRANSITION
# ------------------------------------------------------------

if first_lmc_transition is not None:

    ax.axvline(
        first_lmc_transition,
        linestyle="-.",
        linewidth=1.3,
        label=(
            "First LMC transition "
            f"(round {first_lmc_transition})"
        ),
    )


if all_lmc_transition is not None:

    ax.axvline(
        all_lmc_transition,
        linestyle="-.",
        linewidth=1.3,
        label=(
            "All LMC transitioned "
            f"(round {all_lmc_transition})"
        ),
    )


# ------------------------------------------------------------
# AXES
# ------------------------------------------------------------

ax.set_xlim(
    0,
    NUM_ROUNDS,
)

ax.set_ylim(
    0,
    1.02,
)

ax.set_xlabel(
    "Communication round"
)

ax.set_ylabel(
    r"LMC belief $P_i$"
)

ax.set_title(
    "LMC belief evolution under heterogeneous charging"
)

ax.grid(
    alpha=0.25,
    linewidth=0.7,
)

ax.set_axisbelow(True)


# ------------------------------------------------------------
# LEGEND
# ------------------------------------------------------------

ax.legend(
    loc="lower right",
    frameon=False,
    fontsize=10,
)


fig.tight_layout()


# ============================================================
# SAVE
# ============================================================

fig.savefig(
    OUTPUT_PNG,
    dpi=600,
    bbox_inches="tight",
)

fig.savefig(
    OUTPUT_PDF,
    bbox_inches="tight",
)

plt.show()


print()
print("Saved:")
print(OUTPUT_PNG)
print(OUTPUT_PDF)

# %% [notebook cell 22]
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

# ============================================================
# Plot settings
# ============================================================
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'DejaVu Sans'],
    'mathtext.fontset': 'dejavusans',

    'font.size': 11,
    'axes.titlesize': 13,

    'pdf.fonttype': 42,
    'ps.fonttype': 42,
})

# ============================================================
# Colours
# ============================================================
GREY = '#777777'
DARK = '#222222'


# ============================================================
# Helper functions
# ============================================================
def rounded_box(
    ax,
    x,
    y,
    width,
    height,
    text,
    facecolor,
    edgecolor=DARK,
    fontsize=11,
):
    box = FancyBboxPatch(
        (x, y),
        width,
        height,
        boxstyle='round,pad=0.02',
        facecolor=facecolor,
        edgecolor=edgecolor,
        linewidth=1.2,
        transform=ax.transAxes,
    )

    ax.add_patch(box)

    ax.text(
        x + width / 2,
        y + height / 2,
        text,
        transform=ax.transAxes,
        ha='center',
        va='center',
        fontsize=fontsize,
        linespacing=1.25,
    )


def draw_arrow(ax, start, end):
    arrow = FancyArrowPatch(
        start,
        end,
        arrowstyle='-|>',
        mutation_scale=14,
        linewidth=1.4,
        color=GREY,
        transform=ax.transAxes,
    )

    ax.add_patch(arrow)


# ============================================================
# Figure
# ============================================================
fig, ax = plt.subplots(figsize=(12, 4.5))

ax.set_axis_off()
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)

# Voting task
rounded_box(
    ax,
    0.03,
    0.54,
    0.25,
    0.30,
    (
        'Voting task\n'
        'task-specific voting\n'
        'completion condition'
    ),
    '#DCEEFF',
)

# Battery task
rounded_box(
    ax,
    0.03,
    0.10,
    0.25,
    0.30,
    (
        'Battery task\n'
        'battery reaches the\n'
        'local threshold'
    ),
    '#FFF0D7',
)

# Local-completion interface
rounded_box(
    ax,
    0.39,
    0.33,
    0.22,
    0.28,
    (
        'Local completion\n'
        r'$s_i\in\{0,1\}$'
    ),
    '#F1F1F1',
)

# Shared LMC layer
rounded_box(
    ax,
    0.72,
    0.33,
    0.24,
    0.28,
    (
        'Shared LMC layer\n'
        r'$P_i^{t+1}$ update'
    ),
    '#EADCF4',
)

# Arrows
draw_arrow(
    ax,
    (0.28, 0.69),
    (0.39, 0.52),
)

draw_arrow(
    ax,
    (0.28, 0.25),
    (0.39, 0.42),
)

draw_arrow(
    ax,
    (0.61, 0.47),
    (0.72, 0.47),
)

# Figure heading
ax.text(
    0.50,
    0.90,
    'Task-specific definitions feed the same collective-detection mechanism',
    transform=ax.transAxes,
    ha='center',
    va='center',
    fontsize=13,
    fontweight='bold',
)

plt.tight_layout()

# Optional: save publication-quality versions
# plt.savefig(
#     'experimental_schematic.pdf',
#     bbox_inches='tight',
#     pad_inches=0.05,
# )
# plt.savefig(
#     'experimental_schematic.png',
#     dpi=300,
#     bbox_inches='tight',
#     pad_inches=0.05,
# )

plt.show()

# %% [notebook cell 24]
import numpy as np
import matplotlib.pyplot as plt

plt.rcParams.update({

    'font.size': 14,
    'axes.labelsize': 16,
    'axes.titlesize': 18,
    'xtick.labelsize': 14,
    'ytick.labelsize': 14,
    'legend.fontsize': 12,
    'figure.titlesize': 18,


    'lines.linewidth': 1.5,
    'lines.markersize': 6,

    'axes.grid': True,
    'grid.alpha': 0.3,
    'grid.linestyle': '--',
    'grid.linewidth': 0.8,
})

# -------- Parameters --------
num_agents = 100
n_unfinished = 1  # Changed from 1 to 10
num_rounds = 2000
k1 = 0.5
k2 = 0.43
flag = False
final_round = num_rounds  # Default value if no consensus is reached
error_convergence_occurred = False
error_convergence_round = -1
error_agent_index = -1

# Set completion rounds - last n_unfinished agents never complete
completion_rounds = np.random.randint(1, 11, size=num_agents)
# Last n_unfinished agents have completion round set beyond simulation time
unfinished_indices = list(range(num_agents - n_unfinished, num_agents))
for idx in unfinished_indices:
    completion_rounds[idx] = num_rounds + 1  # Ensure they never complete

s = np.zeros(num_agents, dtype=int)
P_all = np.zeros(num_agents)

history = np.zeros((num_agents, num_rounds))

# -------- Simulation --------
for t in range(num_rounds):

    # Update agent states
    for i in range(num_agents):
        if t >= completion_rounds[i]:
            s[i] = 1  # Agent completes at its designated round
        else:
            s[i] = 0  # Agent still working

    # Update beliefs
    for i in range(num_agents):
        j = np.random.choice([idx for idx in range(num_agents) if idx != i])

        if s[i] == 0:
            P_new = 0
        else:
            P_new = (k1 * P_all[i] + k2 * P_all[j] + (1 - k1 - k2) * s[i]) * s[i]

        P_all[i] = P_new

    history[:, t] = P_all.copy()  # Use copy() to avoid reference issues

    # Check for error convergence (ANY single agent converging to 0.99)
    for i in range(num_agents):
        if P_all[i] >= 0.99:  # Any agent reaching 0.99 is considered error convergence
            error_convergence_occurred = True
            error_convergence_round = t
            error_agent_index = i
            print(f"  ERROR CONVERGENCE DETECTED at round {t}!")
            print(f"    Agent {i} converged to belief={P_all[i]:.4f}")
            print(f"    Agent completion round: {completion_rounds[i]}")
            print(f"    Agent status: {'UNFINISHED' if i in unfinished_indices else 'FINISHED'}")
            break

    if error_convergence_occurred:
        break  # Stop simulation immediately

    # Check for correct consensus (all agents reach high belief after completion)
    if np.all(P_all >= 0.99) and not flag:
        # Verify that this is a legitimate consensus (all agents should have completed)
        legitimate_consensus = True
        for i in range(num_agents):
            if completion_rounds[i] > t:  # Agent hasn't actually completed yet
                legitimate_consensus = False
                break

        if legitimate_consensus:
            final_round = t
            flag = True
            print(f"✅ LEGITIMATE CONSENSUS reached at round {t}")
            break

# -------- Results --------
plt.figure(figsize=(8, 6))

# Determine how many rounds to plot (stopped early or full simulation)
plot_rounds = error_convergence_round + 1 if error_convergence_occurred else num_rounds

# Plot finished agents (first 90 agents)
for i in range(num_agents - n_unfinished):
    plt.plot(history[i, :plot_rounds], alpha=0.7, linewidth=1,
             label=f"Agent {i} (finish@{completion_rounds[i]})" if i < 10 else "")

# Plot unfinished agents (last 10 agents) in red
for i in range(num_agents - n_unfinished, num_agents):
    plt.plot(history[i, :plot_rounds], alpha=0.7, linewidth=1, color='red',
             label=f"Agent {i} (unfinished)" if i < num_agents - n_unfinished + 5 else "")

# Mark the error convergence point if it occurred
if error_convergence_occurred:
    plt.axvline(x=error_convergence_round, color='red', linestyle='--', linewidth=2,
                label=f'Error Convergence (Agent {error_agent_index})')
    plt.plot(error_convergence_round, history[error_agent_index, error_convergence_round],
             'ro', markersize=8, label=f'Error Agent {error_agent_index}')

plt.title(f"Meta-Consensus Simulation (k1={k1}, k2={k2}, {num_agents} agents, {n_unfinished} unfinished)")
plt.xlabel("Round")
plt.ylabel("Belief P_all")
plt.grid(alpha=0.3)
plt.tight_layout()
plt.show()

# -------- Statistics --------
print(f"\n=== Simulation Results ===")
print(f"Total agents: {num_agents}")
print(f"Unfinished agents: {n_unfinished}")
print(f"Finished agents: {num_agents - n_unfinished}")

if error_convergence_occurred:
    print(f"❌ ERROR CONVERGENCE DETECTED!")
    print(f"   - Round: {error_convergence_round}")
    print(f"   - Agent: {error_agent_index}")
    print(f"   - Agent belief: {P_all[error_agent_index]:.4f}")
    print(f"   - Agent completion round: {completion_rounds[error_agent_index]}")
    print(f"   - Agent status: {'UNFINISHED' if error_agent_index in unfinished_indices else 'FINISHED'}")
    print(f"   - Simulation stopped early")
elif flag:
    print(f"✅ LEGITIMATE CONSENSUS reached at round {final_round}")
else:
    print(f"  No consensus reached within {num_rounds} rounds")

print(f"\nCompletion rounds for first 10 finished agents: {completion_rounds[:10]}")
print(f"Unfinished agent indices: {unfinished_indices}")

# Final belief statistics
print(f"\nFinal belief statistics (at round {plot_rounds-1}):")
print(f"  Mean: {np.mean(P_all):.4f}")
print(f"  Std: {np.std(P_all):.4f}")
print(f"  Min: {np.min(P_all):.4f}")
print(f"  Max: {np.max(P_all):.4f}")

# Count agents with high belief
high_belief_agents = np.sum(P_all >= 0.9)
print(f"Agents with belief >= 0.9: {high_belief_agents}/{num_agents}")

# Check unfinished agents' final beliefs
unfinished_final_beliefs = P_all[unfinished_indices]
print(f"Unfinished agents final beliefs: {[f'{x:.4f}' for x in unfinished_final_beliefs]}")

# Additional analysis
if error_convergence_occurred:
    # Count how many agents reached high belief at the time of error
    high_belief_at_error = np.sum(history[:, error_convergence_round] >= 0.9)
    print(f"\nAt error convergence (round {error_convergence_round}):")
    print(f"  Agents with belief >= 0.9: {high_belief_at_error}/{num_agents}")
    print(f"  Agents with belief >= 0.99: {np.sum(history[:, error_convergence_round] >= 0.99)}/{num_agents}")

# %% [notebook cell 26]
"""Targeted finite-horizon tests for Linear Meta-Completion (LMC).

The implementation matches the sequential update schedule used for the
agent-based parameter maps in the manuscript:

* robots update in index order within each communication round;
* receiver i samples one uniformly random partner j != i;
* updates are in place, so later receivers can read beliefs updated earlier
  in the same round;
* all beliefs start at zero;
* one threshold crossing is sufficient to count a detection event.

The script reports run-level event counts rather than robot-averaged values.
"""

# from __future__ import annotations

import numpy as np


N = 100
T = 200
N_RUNS = 1000
THETA = 0.99
MASTER_SEED = 20260921


def run_lmc_batch(
    *,
    completed_count: int,
    k1: float,
    k2: float,
    n_runs: int,
    n_robots: int,
    horizon: int,
    theta: float,
    seed: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Run independent LMC trials in parallel.

    Returns
    -------
    any_crossing:
        Boolean array of length n_runs. True when at least one robot crossed
        theta at least once during that run.
    every_robot_crossed:
        Boolean array of length n_runs. True when every robot crossed theta
        at least once by the end of that run.
    crossed:
        Boolean array with shape (n_runs, n_robots), recording whether each
        robot crossed theta at least once during its run.
    """

    if not 0 <= completed_count <= n_robots:
        raise ValueError("completed_count must lie between 0 and n_robots")
    if k1 <= 0 or k2 <= 0 or k1 + k2 >= 1:
        raise ValueError("Require k1 > 0, k2 > 0, and k1 + k2 < 1")

    rng = np.random.default_rng(seed)
    beliefs = np.zeros((n_runs, n_robots), dtype=np.float64)
    crossed = np.zeros((n_runs, n_robots), dtype=bool)

    # The first completed_count robots are complete. Remaining robots are
    # permanently unfinished and are reset to zero whenever they update.
    states = np.zeros(n_robots, dtype=np.float64)
    states[:completed_count] = 1.0

    run_index = np.arange(n_runs)
    self_growth = 1.0 - k1 - k2

    for _round in range(horizon):
        for i in range(n_robots):
            # Draw uniformly from {0, ..., n_robots - 1} excluding i.
            partners = rng.integers(0, n_robots - 1, size=n_runs)
            partners += partners >= i

            if states[i] == 0.0:
                beliefs[:, i] = 0.0
            else:
                beliefs[:, i] = (
                    k1 * beliefs[:, i]
                    + k2 * beliefs[run_index, partners]
                    + self_growth
                )

            crossed[:, i] |= beliefs[:, i] >= theta

    return crossed.any(axis=1), crossed.all(axis=1), crossed


def strict_boundary_test() -> None:
    """Count premature runs when one of 100 robots remains unfinished."""

    any_crossing, _, crossed = run_lmc_batch(
        completed_count=99,
        k1=0.47,
        k2=0.48,
        n_runs=N_RUNS,
        n_robots=N,
        horizon=T,
        theta=THETA,
        seed=MASTER_SEED,
    )

    premature_runs = int(any_crossing.sum())
    premature_robot_trials = int(crossed[:, :99].sum())
    completed_robot_trials = 99 * N_RUNS
    print("Strict boundary test")
    print(f"N={N}, m=99, k1=0.4, k2=0.55, T={T}, runs={N_RUNS}")
    print(f"Runs with >=1 premature crossing: {premature_runs}/{N_RUNS}")
    print(f"Runs without a premature crossing: {N_RUNS - premature_runs}/{N_RUNS}")
    print(
        "Completed robot-runs with a premature crossing: "
        f"{premature_robot_trials}/{completed_robot_trials}"
    )
    if premature_runs == 0:
        print(f"Rule-of-three approximate 95% upper bound: {3 / N_RUNS:.6f}")
    print()


def full_completion_test() -> None:
    """Count runs in which not every robot crossed by the finite horizon."""

    _, every_robot_crossed, crossed = run_lmc_batch(
        completed_count=100,
        k1=0.47,
        k2=0.48,
        n_runs=N_RUNS,
        n_robots=N,
        horizon=T,
        theta=THETA,
        seed=MASTER_SEED + 1,
    )

    failed_runs = int((~every_robot_crossed).sum())
    undetected_robot_trials = int((~crossed).sum())
    robot_trials = N * N_RUNS
    print("Full-completion test")
    print(f"N={N}, m=100, k1=0.4, k2=0.55, T={T}, runs={N_RUNS}")
    print(f"Runs in which not every robot crossed by T: {failed_runs}/{N_RUNS}")
    print(f"Runs in which every robot crossed by T: {N_RUNS - failed_runs}/{N_RUNS}")
    print(f"Robot-runs that did not cross by T: {undetected_robot_trials}/{robot_trials}")


if __name__ == "__main__":
    strict_boundary_test()
    full_completion_test()

# %% [notebook cell 27]
"""Targeted finite-horizon tests for LMC with 10-round confirmation.

The implementation matches the sequential update schedule used for the
agent-based parameter maps in the manuscript:

* robots update in index order within each communication round;
* receiver i samples one uniformly random partner j != i;
* updates are in place, so later receivers can read beliefs updated earlier
  in the same round;
* all beliefs start at zero;
* a robot transitions only after 10 consecutive rounds at or above theta.

The script reports independent run-level outcomes rather than averages over
robots. It also reports first- and all-robot confirmation times under full
completion.
"""

# from __future__ import annotations

import numpy as np


N = 100
T = 200
N_RUNS = 1000
THETA = 0.99
CONFIRMATION_ROUNDS = 10
K1 = 0.40
K2 = 0.53
MASTER_SEED = 20260921


def run_lmc_batch(
    *,
    completed_count: int,
    k1: float,
    k2: float,
    n_runs: int,
    n_robots: int,
    horizon: int,
    theta: float,
    confirmation_rounds: int,
    seed: int,
) -> dict[str, np.ndarray]:
    """Run independent LMC trials in parallel.

    Confirmation counters are robot-specific. A counter increases by one
    when that robot's updated belief is at or above theta and resets to zero
    when its updated belief falls below theta. Confirmation is irreversible
    after the counter reaches confirmation_rounds.
    """

    if not 0 <= completed_count <= n_robots:
        raise ValueError("completed_count must lie between 0 and n_robots")
    if k1 <= 0 or k2 <= 0 or k1 + k2 >= 1:
        raise ValueError("Require k1 > 0, k2 > 0, and k1 + k2 < 1")
    if confirmation_rounds < 1:
        raise ValueError("confirmation_rounds must be at least 1")

    rng = np.random.default_rng(seed)
    beliefs = np.zeros((n_runs, n_robots), dtype=np.float64)
    consecutive = np.zeros((n_runs, n_robots), dtype=np.uint16)
    confirmed = np.zeros((n_runs, n_robots), dtype=bool)

    first_confirmation_round = np.full(n_runs, -1, dtype=np.int32)
    all_confirmation_round = np.full(n_runs, -1, dtype=np.int32)

    states = np.zeros(n_robots, dtype=np.float64)
    states[:completed_count] = 1.0

    run_index = np.arange(n_runs)
    self_growth = 1.0 - k1 - k2

    for round_number in range(1, horizon + 1):
        for i in range(n_robots):
            partners = rng.integers(0, n_robots - 1, size=n_runs)
            partners += partners >= i

            if states[i] == 0.0:
                beliefs[:, i] = 0.0
            else:
                beliefs[:, i] = (
                    k1 * beliefs[:, i]
                    + k2 * beliefs[run_index, partners]
                    + self_growth
                )

            above = beliefs[:, i] >= theta
            consecutive[:, i] = np.where(
                above,
                np.minimum(consecutive[:, i] + 1, confirmation_rounds),
                0,
            )
            confirmed[:, i] |= consecutive[:, i] >= confirmation_rounds

        any_confirmed = confirmed.any(axis=1)
        newly_first = (first_confirmation_round < 0) & any_confirmed
        first_confirmation_round[newly_first] = round_number

        every_robot_confirmed = confirmed.all(axis=1)
        newly_all = (all_confirmation_round < 0) & every_robot_confirmed
        all_confirmation_round[newly_all] = round_number

    return {
        "any_confirmed": confirmed.any(axis=1),
        "every_robot_confirmed": confirmed.all(axis=1),
        "confirmed": confirmed,
        "first_confirmation_round": first_confirmation_round,
        "all_confirmation_round": all_confirmation_round,
    }


def summarize_observed(values: np.ndarray) -> str:
    """Return median and range after excluding unobserved values (-1)."""

    observed = values[values >= 0]
    if observed.size == 0:
        return "not observed in any run"
    return (
        f"median={np.median(observed):.1f}, "
        f"range={observed.min()}-{observed.max()}"
    )


def strict_boundary_test() -> None:
    """Count premature confirmations with one permanently unfinished robot."""

    result = run_lmc_batch(
        completed_count=99,
        k1=K1,
        k2=K2,
        n_runs=N_RUNS,
        n_robots=N,
        horizon=T,
        theta=THETA,
        confirmation_rounds=CONFIRMATION_ROUNDS,
        seed=MASTER_SEED,
    )

    premature_runs = int(result["any_confirmed"].sum())
    premature_robot_runs = int(result["confirmed"][:, :99].sum())
    completed_robot_runs = 99 * N_RUNS

    print("Strict-boundary test with 10-round confirmation")
    print(
        f"N={N}, m=99, k1={K1:.2f}, k2={K2:.2f}, "
        f"T={T}, runs={N_RUNS}"
    )
    print(f"Runs with >=1 premature transition: {premature_runs}/{N_RUNS}")
    print(
        "Runs without a premature transition: "
        f"{N_RUNS - premature_runs}/{N_RUNS}"
    )
    print(
        "Completed robot-runs with a premature transition: "
        f"{premature_robot_runs}/{completed_robot_runs}"
    )
    if premature_runs == 0:
        print(
            "Rule-of-three approximate 95% upper bound per run: "
            f"{3 / N_RUNS:.6f}"
        )
    print()


def full_completion_test() -> None:
    """Test whether every robot confirms full completion by the horizon."""

    result = run_lmc_batch(
        completed_count=100,
        k1=K1,
        k2=K2,
        n_runs=N_RUNS,
        n_robots=N,
        horizon=T,
        theta=THETA,
        confirmation_rounds=CONFIRMATION_ROUNDS,
        seed=MASTER_SEED + 1,
    )

    failed_runs = int((~result["every_robot_confirmed"]).sum())
    undetected_robot_runs = int((~result["confirmed"]).sum())
    robot_runs = N * N_RUNS

    print("Full-completion test with 10-round confirmation")
    print(
        f"N={N}, m=100, k1={K1:.2f}, k2={K2:.2f}, "
        f"T={T}, runs={N_RUNS}"
    )
    print(f"Runs in which not every robot confirmed by T: {failed_runs}/{N_RUNS}")
    print(
        "Runs in which every robot confirmed by T: "
        f"{N_RUNS - failed_runs}/{N_RUNS}"
    )
    print(
        f"Robot-runs not confirmed by T: {undetected_robot_runs}/{robot_runs}"
    )
    print(
        "First robot confirmation round: "
        + summarize_observed(result["first_confirmation_round"])
    )
    print(
        "All robots confirmation round: "
        + summarize_observed(result["all_confirmation_round"])
    )


if __name__ == "__main__":
    strict_boundary_test()
    full_completion_test()

