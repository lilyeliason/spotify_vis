"""Aggregations used by the summary and the charts.

All functions expect music-only data with the columns added by `load.load_history`.
Rankings use minutes listened (all rows); play counts use only rows where
`is_play` is True.
"""

from dataclasses import dataclass

import pandas as pd

from spotify_viz import config


@dataclass(frozen=True)
class Entity:
    """A thing to rank: which columns identify it and how to name it."""

    keys: tuple[str, ...]
    singular: str
    plural: str

    @property
    def has_artist(self) -> bool:
        return len(self.keys) > 1


ARTIST = Entity((config.ARTIST,), "Artist", "Artists")
# Songs and albums are keyed by name plus primary artist, which merges single
# and album versions while keeping same-titled songs by different artists apart.
SONG = Entity((config.TRACK, config.ARTIST), "Song", "Songs")
ALBUM = Entity((config.ALBUM, config.ARTIST), "Album", "Albums")
ENTITIES = [ARTIST, SONG, ALBUM]


def _label(name: str, artist: str | None) -> str:
    return name if artist is None else f"{name} by {artist}"


def top_items(df: pd.DataFrame, entity: Entity, n: int = config.TOP_N) -> pd.DataFrame:
    """Top `n` items by minutes listened.

    Returns columns: name, artist (None for artists), label, minutes, hours, plays.
    """
    grouped = df.groupby(list(entity.keys)).agg(
        minutes=("minutes_played", "sum"), plays=("is_play", "sum")
    )
    top = grouped.sort_values("minutes", ascending=False).head(n).reset_index()
    top["name"] = top[entity.keys[0]]
    top["artist"] = top[config.ARTIST] if entity.has_artist else None
    top["label"] = [_label(nm, ar) for nm, ar in zip(top["name"], top["artist"])]
    top["hours"] = top["minutes"] / 60
    top["plays"] = top["plays"].astype(int)
    return top[["name", "artist", "label", "minutes", "hours", "plays"]]


def totals(df: pd.DataFrame) -> dict[str, float]:
    """Overall plays (above threshold) and minutes (all rows)."""
    minutes = df["minutes_played"].sum()
    return {"plays": int(df["is_play"].sum()), "minutes": minutes, "hours": minutes / 60}


def plays_by_month(df: pd.DataFrame) -> pd.Series:
    """Plays per local calendar month, with empty months filled with 0."""
    counts = df[df["is_play"]].groupby("year_month").size()
    months = pd.period_range(df["year_month"].min(), df["year_month"].max(), freq="M")
    return counts.reindex(months, fill_value=0)


def plays_by_year(df: pd.DataFrame) -> pd.Series:
    """Plays per local calendar year, with empty years filled with 0."""
    counts = df[df["is_play"]].groupby("year").size()
    years = range(df["year"].min(), df["year"].max() + 1)
    return counts.reindex(years, fill_value=0)


def monthly_series(
    df: pd.DataFrame, entity: Entity, metric: str, n: int = config.STREAM_ITEM_COUNT
) -> pd.DataFrame:
    """Monthly totals for the top `n` items (ranked by minutes).

    `metric` is "minutes" or "plays". Returns one column per item label, in
    rank order, indexed by month start over the full date range (gaps are 0).
    """
    top = top_items(df, entity, n)
    keys = list(entity.keys)
    top_keys = top[["name", "artist"]].iloc[:, : len(keys)].set_axis(keys, axis=1)
    df_top = df.merge(top_keys, on=keys)

    if metric == "minutes":
        values = df_top.groupby(keys + ["year_month"])["minutes_played"].sum()
    elif metric == "plays":
        values = df_top[df_top["is_play"]].groupby(keys + ["year_month"]).size()
    else:
        raise ValueError(f"Unknown metric: {metric}")

    wide = values.unstack(keys, fill_value=0)
    months = pd.period_range(df["year_month"].min(), df["year_month"].max(), freq="M")
    wide = wide.reindex(months, fill_value=0)

    # Order columns by rank and rename them to display labels.
    ordered = [tuple(row) if len(keys) > 1 else row[0] for row in top_keys.itertuples(index=False)]
    wide = wide.reindex(columns=ordered, fill_value=0)
    wide.columns = top["label"].tolist()
    wide.index = wide.index.to_timestamp()
    return wide.astype(float)
