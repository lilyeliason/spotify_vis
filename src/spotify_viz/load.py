"""Read Spotify Extended Streaming History JSON, clean it, and cache it to Parquet."""

import json
from pathlib import Path

import pandas as pd

from spotify_viz import config

# Bump when the cleaned schema changes so old caches are rebuilt.
CACHE_VERSION = 1


def find_raw_files(source_dir: Path) -> list[Path]:
    """Return the audio history JSON files in a folder, sorted by name."""
    return sorted(source_dir.glob(config.RAW_FILE_GLOB))


def read_raw(files: list[Path]) -> pd.DataFrame:
    """Read and concatenate the given JSON files, one row per stream."""
    records: list[dict] = []
    for path in files:
        with open(path, "r", encoding="utf-8") as f:
            records.extend(json.load(f))
    return pd.DataFrame(records)


def _content_type(df: pd.DataFrame) -> pd.Series:
    """Label each row as music, podcast, audiobook, or unknown."""
    content = pd.Series("unknown", index=df.index)
    if "audiobook_title" in df.columns:
        content[df["audiobook_title"].notna()] = "audiobook"
    if "episode_name" in df.columns:
        content[df["episode_name"].notna()] = "podcast"
    content[df[config.TRACK].notna()] = "music"
    return content


def clean(raw: pd.DataFrame) -> pd.DataFrame:
    """Drop identifying fields, parse timestamps (UTC), and flag content type."""
    df = raw.drop(columns=[c for c in config.IDENTIFYING_FIELDS if c in raw.columns])
    df["ts"] = pd.to_datetime(df["ts"], utc=True)
    df["content_type"] = _content_type(df)
    df["is_music"] = df["content_type"] == "music"
    return df.sort_values("ts").reset_index(drop=True)


def _manifest(files: list[Path]) -> dict:
    """Describe the raw inputs so a stale cache can be detected."""
    return {
        "cache_version": CACHE_VERSION,
        "files": {p.name: p.stat().st_mtime_ns for p in files},
    }


def load_clean(source_dir: Path, cache_name: str, refresh: bool = False) -> pd.DataFrame:
    """Return cleaned history from `source_dir`, using the Parquet cache when valid.

    The cache is rebuilt when file names or modification times change, or
    when `refresh` is True. Cached timestamps are UTC.
    """
    files = find_raw_files(source_dir)
    if not files:
        raise FileNotFoundError(
            f"No files matching {config.RAW_FILE_GLOB} in {source_dir}"
        )

    config.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    cache_path = config.PROCESSED_DIR / f"{cache_name}.parquet"
    manifest_path = config.PROCESSED_DIR / f"{cache_name}.manifest.json"
    manifest = _manifest(files)

    if not refresh and cache_path.exists() and manifest_path.exists():
        if json.loads(manifest_path.read_text()) == manifest:
            print(f"Loaded cached data from {cache_path.name}")
            return pd.read_parquet(cache_path)

    print(f"Parsing {len(files)} raw file(s) from {source_dir}")
    df = clean(read_raw(files))
    df.to_parquet(cache_path, index=False)
    manifest_path.write_text(json.dumps(manifest, indent=2))
    return df


def add_time_columns(df: pd.DataFrame, timezone: str = config.TIMEZONE) -> pd.DataFrame:
    """Convert UTC timestamps to `timezone` and derive date parts from local time."""
    df = df.copy()
    local = df["ts"].dt.tz_convert(timezone)
    df["ts_local"] = local
    df["date"] = local.dt.date
    df["hour"] = local.dt.hour
    df["day_of_week"] = local.dt.day_name()
    df["month"] = local.dt.month
    df["year"] = local.dt.year
    df["year_month"] = local.dt.tz_localize(None).dt.to_period("M")
    return df


def add_play_columns(df: pd.DataFrame, min_play_ms: int = config.MIN_PLAY_MS) -> pd.DataFrame:
    """Add minutes played (all rows) and an `is_play` flag (rows at or above the threshold)."""
    df = df.copy()
    df["minutes_played"] = df["ms_played"] / 60_000
    df["is_play"] = df["ms_played"] >= min_play_ms
    return df


def music_only(df: pd.DataFrame) -> pd.DataFrame:
    """Keep only music rows, printing how many non-music rows were excluded."""
    excluded = df[~df["is_music"]]
    breakdown = ", ".join(
        f"{n:,} {kind}" for kind, n in excluded["content_type"].value_counts().items()
    )
    print(f"Excluded {len(excluded):,} non-music rows ({breakdown or 'none'})")
    return df[df["is_music"]].copy()


def load_history(refresh: bool = False, sample: bool = False) -> pd.DataFrame:
    """Load cleaned history with local-time and play columns added.

    Includes all content types; use `music_only` for music analyses.
    """
    if sample:
        df = load_clean(config.SAMPLE_DIR, "sample", refresh=refresh)
    else:
        df = load_clean(config.RAW_DIR, "streaming_history", refresh=refresh)
    print(f"Loaded {len(df):,} rows")
    return add_play_columns(add_time_columns(df))
