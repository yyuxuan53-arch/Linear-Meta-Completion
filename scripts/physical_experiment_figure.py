from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from PIL import Image


# ============================================================
# Final publication dimensions and typography
# ============================================================
FIG_WIDTH_CM = 18.4
FIG_HEIGHT_CM = 11.2

mpl.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "font.size": 9,
    "axes.titlesize": 9,
    "axes.labelsize": 9,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "svg.fonttype": "none",
    "figure.facecolor": "white",
})


# ============================================================
# Read the three representative Random-walk images already in Colab
# ============================================================
IMAGE_FILES = {
    "running": "randomwalk1.png",
    "finished": "randomwalk2.png",
    "metacompletion": "randomwalk3.png",
}

def find_uploaded_file(filename):
    """Find the newest Colab copy, including names such as 'file (1).png'."""
    requested = Path(filename)
    candidates = list(Path("/content").glob(
        f"{requested.stem}*{requested.suffix}"
    ))
    if not candidates:
        raise FileNotFoundError(
            f"Cannot find {filename} in /content. Upload it in Colab first."
        )
    return max(candidates, key=lambda path: path.stat().st_mtime)


resolved_files = {
    key: find_uploaded_file(filename)
    for key, filename in IMAGE_FILES.items()
}

images = {
    key: Image.open(path).convert("RGB")
    for key, path in resolved_files.items()
}

print("Using these uploaded files:")
for key, path in resolved_files.items():
    print(f"  {key}: {path.name}")


# ============================================================
# Original physical-outcomes table from the supplied manuscript.
# The wording and values are retained; only line wrapping is added.
# ============================================================
SUMMARY_ROWS = [
    ("Random walk", "LMC, all finished", "21", "89", "125", "104",
     "All robots transitioned"),
    ("Random walk", "LMC, one unfinished", "--", "--", "--", "--",
     "No transition detected"),
    ("Battery", "LMC, all finished", "106", "140", "141", "35",
     "All scorable robots\ntransitioned"),
    ("Battery", "LMC, one unfinished", "--", "--", "--", "--",
     "No transition detected"),
    ("Voting", "LMC, all finished", "112", "176", "177", "65",
     "All scorable robots\ntransitioned"),
]


# ============================================================
# Figure layout
# ============================================================
fig = plt.figure(
    figsize=(FIG_WIDTH_CM / 2.54, FIG_HEIGHT_CM / 2.54),
    facecolor="white",
)

grid = fig.add_gridspec(
    nrows=2,
    ncols=3,
    height_ratios=[1.10, 1.22],
    left=0.025,
    right=0.99,
    bottom=0.045,
    top=0.945,
    wspace=0.035,
    hspace=0.13,
)


# ============================================================
# Panels A-C: representative Random-walk sequence
# ============================================================
photo_panels = [
    (
        "running",
        "A",
        "Task in progress",
        "Yellow: ongoing task",
    ),
    (
        "finished",
        "B",
        "All robots locally complete",
        "Green: local completion",
    ),
    (
        "metacompletion",
        "C",
        "Collective completion detected",
        "Blue: LMC detection",
    ),
]

for column, (key, letter, title, subtitle) in enumerate(photo_panels):
    ax = fig.add_subplot(grid[0, column])

    # Preserve the complete original image without colour adjustment,
    # sharpening, cropping, or generative processing.
    ax.imshow(images[key], interpolation="none")
    ax.set_axis_off()

    ax.text(
        0.00,
        1.075,
        letter,
        transform=ax.transAxes,
        fontsize=10,
        fontweight="bold",
        ha="left",
        va="bottom",
        clip_on=False,
    )
    ax.text(
        0.10,
        1.075,
        title,
        transform=ax.transAxes,
        fontsize=9,
        fontweight="bold",
        ha="left",
        va="bottom",
        clip_on=False,
    )
    ax.text(
        0.00,
        0.995,
        subtitle,
        transform=ax.transAxes,
        fontsize=9,
        ha="left",
        va="bottom",
        clip_on=False,
    )


# ============================================================
# Panel D: graphical summary of all three physical demonstrations
# ============================================================
ax = fig.add_subplot(grid[1, :])
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis("off")

ax.text(
    0.00,
    0.985,
    "D",
    transform=ax.transAxes,
    fontsize=10,
    fontweight="bold",
    ha="left",
    va="bottom",
)
ax.text(
    0.035,
    0.985,
    "Experimental summary",
    transform=ax.transAxes,
    fontsize=9,
    fontweight="bold",
    ha="left",
    va="bottom",
)

# The column wording and row contents reproduce the original manuscript
# table. Long headings/cells are wrapped only to fit the final page width.
column_x = [0.005, 0.135, 0.385, 0.520, 0.625, 0.735, 0.825]
headers = [
    "Task",
    "Condition",
    "Observed local\ncompletion\n(s)",
    "First\ndetection\n(s)",
    "Final\ndetection\n(s)",
    "Final-detection\ndelay\n(s)",
    "Outcome",
]

# Text columns are left-aligned inside fixed column boundaries; numerical
# columns remain centered. This prevents long labels from spilling into
# adjacent cells while preserving the 9-pt minimum type size.
header_alignments = ["left", "left", "center", "center", "center", "center", "left"]
cell_alignments = ["left", "left", "center", "center", "center", "center", "left"]

header_y = 0.82
for x, header, alignment in zip(column_x, headers, header_alignments):
    ax.text(
        x,
        header_y,
        header,
        fontsize=9,
        fontweight="bold",
        ha=alignment,
        va="center",
        linespacing=1.08,
    )

# Minimal horizontal rules make this a clean summary panel rather than
# a screenshot of a formal manuscript table.
ax.plot([0.005, 0.995], [0.94, 0.94], color="black", linewidth=0.8)
ax.plot([0.005, 0.995], [0.69, 0.69], color="black", linewidth=0.6)

row_y = [0.60, 0.47, 0.34, 0.21, 0.08]
for index, (row, y) in enumerate(zip(SUMMARY_ROWS, row_y)):
    values = list(row)
    for x, value, alignment in zip(column_x, values, cell_alignments):
        ax.text(
            x,
            y,
            value,
            fontsize=9,
            ha=alignment,
            va="center",
            linespacing=1.0,
        )

    if index < len(SUMMARY_ROWS) - 1:
        separator_y = (row_y[index] + row_y[index + 1]) / 2
        ax.plot(
            [0.01, 0.99],
            [separator_y, separator_y],
            color="#B8B8B8",
            linewidth=0.45,
        )

ax.plot([0.005, 0.995], [0.015, 0.015], color="black", linewidth=0.8)


# ============================================================
# Display only; save manually from the Colab output if desired
# ============================================================
plt.show()

print(
    f"Final figure size: {FIG_WIDTH_CM:.1f} x {FIG_HEIGHT_CM:.1f} cm. "
    "All displayed text is at least 9 pt."
)

