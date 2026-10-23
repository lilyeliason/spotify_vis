"""Regenerate the text summary and every chart.

Usage:
    python scripts/run_all.py [--refresh] [--sample] [--years 2023 2024]
"""

import argparse

import pandas as pd

from spotify_viz import config, load, metrics, style, summary
from spotify_viz.plots import bars, lines, streamgraphs

PLAY_NOTE = (
    f"A play is a stream of at least {config.MIN_PLAY_MS // 1000} seconds. "
    "Podcasts and audiobooks are excluded"
)
BAR_NOTE = (
    "Ranked by total minutes listened, including skipped streams. "
    "Songs and albums are grouped by name and primary artist"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--refresh", action="store_true", help="re-parse raw JSON even if the cache is current"
    )
    parser.add_argument(
        "--sample", action="store_true", help="use the fake sample data in data/sample/"
    )
    parser.add_argument(
        "--years",
        type=int,
        nargs="+",
        metavar="YEAR",
        help="only generate yearly charts for these years (default: all)",
    )
    return parser.parse_args()


def yearly_bar_charts(df: pd.DataFrame, years: list[int]) -> None:
    """Top artists, songs, and albums for each requested year."""
    for year in years:
        df_year = df[df["year"] == year]
        for entity in metrics.ENTITIES:
            bars.top_items_bar(
                metrics.top_items(df_year, entity),
                title=f"Top {entity.plural} of {year}",
                ylabel=entity.plural,
                filename=f"Top_{entity.plural}_of_{year}.png",
                years=[year],
                note=BAR_NOTE,
            )


def all_time_charts(df: pd.DataFrame, years: list[int]) -> None:
    """All-time top items bars and plays-over-time lines."""
    for entity in metrics.ENTITIES:
        bars.top_items_bar(
            metrics.top_items(df, entity),
            title=f"Top {entity.plural} (All Time)",
            ylabel=entity.plural,
            filename=f"All_Time_Top_{entity.plural}.png",
            years=years,
            note=BAR_NOTE,
        )
    lines.plays_line(
        metrics.plays_by_month(df),
        title="Listening Data By Month (All Time)",
        xlabel="Month",
        filename="All_Time_Listening_By_Month.png",
        years=years,
        note=PLAY_NOTE,
        show_every_nth=6,
    )
    lines.plays_line(
        metrics.plays_by_year(df),
        title="Listening Data By Year (All Time)",
        xlabel="Year",
        filename="All_Time_Listening_By_Year.png",
        years=years,
        note=PLAY_NOTE,
        figsize=(10, 6),
    )


def all_streamgraphs(df: pd.DataFrame, years: list[int]) -> None:
    """Raw, STL trend, and rolling mean streamgraphs for minutes and plays."""
    n = config.STREAM_ITEM_COUNT
    variants = [
        ("Raw Data", "Raw", lambda d: d, "Monthly totals"),
        (
            "STL Trend",
            "STL",
            streamgraphs.stl_trend,
            f"Trend component from STL decomposition, period {config.STL_PERIOD} months, clipped at 0",
        ),
        (
            f"{config.ROLLING_WINDOW}-Month Rolling Mean",
            "Rolling",
            streamgraphs.rolling_mean,
            f"Centered {config.ROLLING_WINDOW}-month rolling mean of monthly totals",
        ),
    ]
    for entity in metrics.ENTITIES:
        print(f"\nProcessing Streamgraphs for: {entity.singular}")
        for metric, unit_name, unit_file, extra in [
            ("minutes", "Minutes Played", "Minutes", ""),
            ("plays", "Plays", "Plays", f" Plays are streams of at least {config.MIN_PLAY_MS // 1000} seconds."),
        ]:
            monthly = metrics.monthly_series(df, entity, metric, n)
            for smooth_title, smooth_file, smooth, smooth_note in variants:
                streamgraphs.streamgraph(
                    smooth(monthly),
                    title=f"{entity.singular} | {unit_name} | {smooth_title} Streamgraph",
                    ylabel=f"Monthly {unit_name} (Symmetric Baseline)",
                    legend_title=f"Top {n} {entity.plural}",
                    filename=f"{entity.singular}_{unit_file}_{smooth_file}_Streamgraph.png",
                    years=years,
                    note=(
                        f"Top {n} {entity.plural.lower()} by total minutes. "
                        f"{smooth_note}.{extra}"
                    ),
                )


def main() -> None:
    args = parse_args()
    style.apply_style()

    history = load.load_history(refresh=args.refresh, sample=args.sample)
    music = load.music_only(history)
    all_years = sorted(int(y) for y in music["year"].unique())

    if args.years:
        missing = sorted(set(args.years) - set(all_years))
        if missing:
            print(f"No data for year(s) {missing}; skipping them.")
        chart_years = [y for y in all_years if y in args.years]
    else:
        chart_years = all_years

    path = summary.write_summary(music)
    print(f"Wrote {path.relative_to(config.PROJECT_ROOT)}")

    yearly_bar_charts(music, chart_years)
    all_time_charts(music, all_years)
    all_streamgraphs(music, all_years)
    print(f"\nAll figures saved to {config.FIGURES_DIR.relative_to(config.PROJECT_ROOT)}/")


if __name__ == "__main__":
    main()
