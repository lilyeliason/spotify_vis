"""Horizontal bar charts of top items."""

import textwrap
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from spotify_viz import style


def _wrap_label(name: str, artist: str | None) -> str:
    if artist is None:
        return textwrap.fill(name, width=35)
    return f"{textwrap.fill(name, width=30)}\n{textwrap.fill(f'by {artist}', width=30)}"


def top_items_bar(
    top: pd.DataFrame,
    title: str,
    ylabel: str,
    filename: str,
    years: list[int],
    note: str,
) -> Path:
    """Plot hours listened for a table from `metrics.top_items`, largest at top."""
    labels = [_wrap_label(n, a) for n, a in zip(top["name"], top["artist"])]

    fig, ax = plt.subplots(figsize=(12, 8))
    ax.barh(range(len(top)), top["hours"], color=style.BAR_COLOR)
    ax.set_yticks(range(len(top)), labels)
    ax.invert_yaxis()
    ax.set_xlabel("Hours Listened")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    fig.tight_layout()

    style.add_chart_note(fig, years, note)
    return style.save_figure(fig, filename)
