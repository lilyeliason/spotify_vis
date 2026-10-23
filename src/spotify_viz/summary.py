"""Plain text listening summary, overall and per year."""

from pathlib import Path
from typing import TextIO

import pandas as pd

from spotify_viz import config, metrics


def _write_section(df: pd.DataFrame, out: TextIO, heading: str) -> None:
    stats = metrics.totals(df)
    seconds = config.MIN_PLAY_MS // 1000
    out.write(f"\n{'=' * 60}\n{heading}\n")
    out.write(f"Total songs played ({seconds}s or longer): {stats['plays']:,}\n")
    out.write(
        f"Total listening time: {stats['minutes']:,.0f} minutes "
        f"({stats['hours']:,.0f} hours)\n"
    )

    for entity in metrics.ENTITIES:
        out.write(f"\nTop {config.TOP_N} {entity.plural} (by Minutes Listened):\n")
        for row in metrics.top_items(df, entity).itertuples():
            name = f"'{row.name}' by {row.artist}" if entity.has_artist else row.name
            out.write(
                f"  • {name}: {row.minutes:,.0f} min ({row.hours:.1f} hrs) "
                f"| {row.plays:,} plays\n"
            )


def write_summary(df: pd.DataFrame, path: Path | None = None) -> Path:
    """Write the all-time summary followed by each year, newest first."""
    path = path or config.SUMMARIES_DIR / config.SUMMARY_FILENAME
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as out:
        _write_section(df, out, "Overall Listening Summary: (All Time)")
        for year in sorted(df["year"].unique(), reverse=True):
            out.write("\n")
            _write_section(df[df["year"] == year], out, f"Yearly Listening Summary: {year}")
    return path
