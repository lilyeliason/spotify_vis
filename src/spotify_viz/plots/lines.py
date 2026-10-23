"""Line charts of plays over time."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from spotify_viz import style


def plays_line(
    series: pd.Series,
    title: str,
    xlabel: str,
    filename: str,
    years: list[int],
    note: str,
    show_every_nth: int = 1,
    figsize: tuple[float, float] = (14, 7),
) -> Path:
    """Plot a play-count series indexed by period (months) or integer years."""
    fig, ax = plt.subplots(figsize=figsize)

    if isinstance(series.index, pd.PeriodIndex):
        x_labels = series.index.astype(str)
        ax.plot(range(len(series)), series.values, color=style.LINE_COLOR)
        ticks = range(0, len(x_labels), show_every_nth)
        ax.set_xticks(ticks, x_labels[::show_every_nth], rotation=45)
    else:
        ax.plot(series.index, series.values, color=style.LINE_COLOR)
        ax.set_xticks(series.index)

    ax.set_xlabel(xlabel)
    ax.set_ylabel("Number of Songs Played")
    ax.set_title(title)
    fig.tight_layout()

    style.add_chart_note(fig, years, note)
    return style.save_figure(fig, filename)
