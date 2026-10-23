"""Matplotlib styling: palette, rcParams, fonts, and shared chart helpers."""

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.figure import Figure

from spotify_viz import config

BACKGROUND = "#F9F9F9"
SPINE_COLOR = "#D8D4CC"
TEXT_COLOR = "#3C3A34"
MUTED_TEXT = "#605E5A"

FONT_STACK = ["Inter", "Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"]

# Shades per hue, dark to light.
PALETTE: dict[str, list[str]] = {
    "teal": ["#275E5C", "#6BAEAC", "#9ED4D1"],
    "red": ["#5C0E08", "#97261F", "#B8594D", "#E38171"],
    "blue": ["#1A446C", "#3C6994", "#6291BF", "#98B8DA"],
    "orange": ["#6A3910", "#9C5824", "#D5762C", "#E8AA7F"],
    "olive": ["#687321", "#8E9C3A", "#B6C643", "#DFEC9F"],
    "gray": ["#3C3A34", "#605E5A", "#86827E", "#B3AA9E", "#D8D4CC"],
}

# Single-color default for bar and line charts.
BAR_COLOR = PALETTE["teal"][1]
LINE_COLOR = PALETTE["teal"][0]

# Streamgraph palette: the six base shades first, then extra shades. The order
# was chosen so neighboring colors stay distinguishable under color vision
# deficiency simulation.
CATEGORICAL_10 = [
    "#97261F",  # red base
    "#3C6994",  # blue base
    "#8E9C3A",  # olive base
    "#605E5A",  # gray base
    "#6BAEAC",  # teal base
    "#9C5824",  # orange base
    "#9ED4D1",  # teal light
    "#275E5C",  # teal dark
    "#5C0E08",  # red dark
    "#B8594D",  # red light
]

_applied = False


def register_fonts(fonts_dir: Path = config.FONTS_DIR) -> int:
    """Register .ttf/.otf files in `fonts_dir` with matplotlib. Returns the count."""
    files = [p for p in fonts_dir.glob("*") if p.suffix.lower() in {".ttf", ".otf"}]
    for path in files:
        font_manager.fontManager.addfont(str(path))
    return len(files)


def apply_style() -> None:
    """Register bundled fonts and set the project's rcParams. Safe to call repeatedly."""
    global _applied
    if _applied:
        return
    if register_fonts() == 0:
        print(
            f"No fonts found in {config.FONTS_DIR}; falling back to "
            "Helvetica Neue, Helvetica, or Arial. See README to install Inter."
        )

    # Keep only stack fonts that are installed so matplotlib does not warn
    # about each missing one.
    installed = {f.name for f in font_manager.fontManager.ttflist}
    fonts = [f for f in FONT_STACK if f in installed] or ["DejaVu Sans"]

    mpl.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": fonts,
            "font.size": 10,
            "text.color": TEXT_COLOR,
            "figure.facecolor": BACKGROUND,
            "axes.facecolor": BACKGROUND,
            "savefig.facecolor": BACKGROUND,
            "axes.edgecolor": SPINE_COLOR,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.labelcolor": TEXT_COLOR,
            "axes.labelsize": 11,
            "axes.titlesize": 14,
            "axes.titleweight": "semibold",
            "axes.titlelocation": "left",
            "axes.titlepad": 14,
            "axes.grid": False,
            "axes.prop_cycle": mpl.cycler(color=CATEGORICAL_10),
            "xtick.color": MUTED_TEXT,
            "ytick.color": MUTED_TEXT,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "legend.frameon": False,
            "legend.fontsize": 9,
            "lines.linewidth": 2,
            "patch.edgecolor": "none",
            "savefig.bbox": "tight",
            "savefig.dpi": 150,
        }
    )
    _applied = True


def year_span(years: list[int]) -> str:
    """Format a year range for chart notes, e.g. '2017 to 2025' or '2023'."""
    first, last = min(years), max(years)
    return str(first) if first == last else f"{first} to {last}"


def add_chart_note(fig: Figure, years: list[int], note: str) -> None:
    """Write the two-line source and note text in the figure's bottom left."""
    text = (
        f"Source: Spotify Extended Streaming History, {year_span(years)}.\n"
        f"Note: {note.rstrip('.')}."
    )
    fig.text(0.01, -0.01, text, ha="left", va="top", fontsize=8, color=MUTED_TEXT)


def save_figure(fig: Figure, filename: str) -> Path:
    """Save a figure to the figures directory and close it."""
    config.FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    path = config.FIGURES_DIR / filename
    fig.savefig(path)
    plt.close(fig)
    return path
