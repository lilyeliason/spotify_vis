"""Streamgraphs of the top items over time, raw and smoothed."""

from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
from statsmodels.tsa.seasonal import STL

from spotify_viz import config, style


def stl_trend(df: pd.DataFrame, period: int = config.STL_PERIOD) -> pd.DataFrame:
    """STL trend per column, clipped at 0. Series shorter than two periods are returned as is."""
    if len(df) < period * 2:
        return df.copy()
    trend = pd.DataFrame(index=df.index)
    for col in df.columns:
        trend[col] = STL(df[col], period=period, robust=True).fit().trend
    return trend.clip(lower=0)


def rolling_mean(df: pd.DataFrame, window: int = config.ROLLING_WINDOW) -> pd.DataFrame:
    """Centered rolling mean over `window` months."""
    return df.rolling(window=window, center=True, min_periods=1).mean()


def streamgraph(
    data: pd.DataFrame,
    title: str,
    ylabel: str,
    legend_title: str,
    filename: str,
    years: list[int],
    note: str,
) -> Path | None:
    """Plot a symmetric-baseline stacked area chart, one band per column."""
    if data.empty or data.to_numpy().sum() == 0:
        print(f"Skipped {filename}: not enough valid data.")
        return None

    fig, ax = plt.subplots(figsize=(16, 9))
    ax.stackplot(
        data.index,
        data.T.values,
        labels=data.columns.tolist(),
        colors=style.CATEGORICAL_10[: len(data.columns)],
        baseline="sym",
    )
    ax.axhline(0, color=style.SPINE_COLOR, linestyle="--", linewidth=0.7)

    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1), title=legend_title)
    ax.margins(0, 0.05)
    fig.tight_layout()

    style.add_chart_note(fig, years, note)
    path = style.save_figure(fig, filename)
    print(f"Generated {filename}")
    return path
