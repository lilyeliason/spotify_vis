import json
import os
import textwrap

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
from statsmodels.tsa.seasonal import seasonal_decompose

"""
Data Loading and Cleaning
- Read all Spotify Streaming History JSON files, combine them, and prepare the data for analysis. 
- This handles common issues like file encoding errors and converts timestamps and milliseconds into usable formats (minutes, dates, years).
"""

folder = "streaming_files"
all_data = []

for file in os.listdir(folder):
    if file.startswith("Streaming_History_Audio") and file.endswith(
        ".json"
    ):  # looing only at audio files and not video files
        filepath = os.path.join(folder, file)

    try:
        with (
            open(filepath, "r", encoding="utf-8", errors="ignore") as f
        ):  # some songs/artist names have special symbols, so we have an encoding/error handling process here
            data = json.load(f)
            all_data.extend(data)
    except Exception as e:
        print(f"Skipped {file}: {e}")

df = pd.DataFrame(all_data)

# these are the only data types i'm using from the JSON file
columns_to_keep = [
    "ts",  # timestamp
    "ms_played",  # miliseconds played
    "master_metadata_track_name",  # song name
    "master_metadata_album_artist_name",  # artist name
    "master_metadata_album_album_name",  # album name
]

existing_columns = [col for col in columns_to_keep if col in df.columns]
df_clean = df[existing_columns].copy()


if "ms_played" in df_clean.columns:
    df_clean["seconds_played"] = df_clean["ms_played"] / 1000
    df_clean["minutes_played"] = df_clean["seconds_played"] / 60

# timestamp conversions for easier analysis
df_clean["ts"] = pd.to_datetime(df_clean["ts"])
df_clean["date"] = df_clean["ts"].dt.date
df_clean["hour"] = df_clean["ts"].dt.hour
df_clean["day_of_week"] = df_clean["ts"].dt.day_name()
df_clean["month"] = df_clean["ts"].dt.month
df_clean["year_month"] = df_clean["ts"].dt.to_period("M")
df_clean["year"] = df_clean["ts"].dt.year


"""
Visualization Helper Functions
- Define reusable functions for generating and styling the different charts: 
    - Horizontal bar charts (for top artists/songs/albums)
    - Line charts (for listening trends over all time).
"""


def filter_year(df, year):
    # Filters the main DataFrame by a specific year
    return df[df["ts"].dt.year == year]


def bar_chart(df, column_name, title, filename, color="#1DB954", include_artist=False):
    # Calculates top 10 items by minutes played and generates a horizontal bar chart.
    item_hours = df.groupby(column_name)["minutes_played"].sum() / 60
    item_hours = item_hours.sort_values(ascending=False).head(10)

    # Create labels
    if include_artist:
        labels = []
        for item in item_hours.index:
            item_data = df[df[column_name] == item]

            primary_artist_series = item_data.groupby(
                "master_metadata_album_artist_name"
            )["minutes_played"].sum()
            artist = (
                primary_artist_series.idxmax()
                if not primary_artist_series.empty
                else "Unknown"
            )
            wrapped_item = textwrap.fill(item, width=30)
            wrapped_artist = textwrap.fill(f"by {artist}", width=30)
            labels.append(f"{wrapped_item}\n{wrapped_artist}")
    else:
        labels = [textwrap.fill(name, width=35) for name in item_hours.index]

    plt.figure(figsize=(12, 8))
    plt.barh(range(len(item_hours)), item_hours.values, color=color)
    plt.yticks(range(len(item_hours)), labels, fontsize=9, fontfamily="monospace")
    plt.xlabel("Hours Listened", fontsize=12, fontfamily="monospace")
    plt.ylabel(title.split()[1], fontsize=12, fontfamily="monospace")
    plt.title(title, fontsize=14, fontfamily="monospace", pad=15)
    plt.gca().invert_yaxis()
    plt.subplots_adjust(left=0.3)
    plt.tight_layout()

    plt.savefig(filename, bbox_inches="tight")
    plt.close()


def line_chart(
    df, groupby_column, title, x_label, filename, show_every_nth=1, figsize=(14, 7)
):  # Added 'filename'
    # Plots listening data over time (month-by-month and year-by-year)
    data = df.groupby(groupby_column).size()

    plt.figure(figsize=figsize)

    if groupby_column == "year_month":
        # Monthly data handling
        plt.plot(data.index.astype(str), data.values, color="#1DB954", linewidth=2.5)
        x_labels = data.index.astype(str)
        plt.xticks(
            range(0, len(x_labels), show_every_nth),
            x_labels[::show_every_nth],
            rotation=45,
            fontsize=10,
        )
    else:
        # Yearly data handling
        min_year = data.index.min()
        max_year = data.index.max()
        all_years = range(min_year, max_year + 1)
        data = data.reindex(all_years, fill_value=0)

        plt.plot(
            data.index,
            data.values,
            color="#1DB954",
            linewidth=2,
        )
        plt.xticks(data.index, fontsize=10)

    plt.xlabel(x_label, fontsize=12, fontfamily="monospace")
    plt.ylabel("Number of Songs Played", fontsize=12, fontfamily="monospace")
    plt.title(title, fontsize=13, fontfamily="monospace", pad=20, loc="left")
    plt.yticks(fontsize=10)

    ax = plt.gca()
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#CCCCCC")
    ax.spines["bottom"].set_color("#CCCCCC")

    plt.tight_layout()

    plt.savefig(filename, bbox_inches="tight")
    plt.close()


"""
Summary Statistics Output
- Generate detailed text summaries of overall and yearly listening habits
- Write the output to a single text file
"""


def write_summary_stats(df, file_handle, year=None):
    # Generate the ranked list and general metrics for a given time frame
    if year:  # filter df to include only specified year
        df = df[df["year"] == year]
        file_handle.write(f"\n\n{'=' * 60}\n")
        file_handle.write(f"Yearly Listening Summary: {year}\n")
    else:  # no year means use entire dataset
        file_handle.write(f"\n{'=' * 60}\n")
        file_handle.write("Overall Listening Summary: (All Time)\n")

    # Overall Calculations
    total_songs = len(df)
    total_minutes = df["minutes_played"].sum()
    total_hours = total_minutes / 60

    file_handle.write(f"Total songs played: {total_songs:,}\n")
    file_handle.write(
        f"Total listening time: {total_minutes:,.0f} minutes ({total_hours:,.0f} hours)\n"
    )

    # Top 10 Artists
    file_handle.write("\nTop 10 Artists (by Minutes Listened):\n")
    top_10_artists = (
        df.groupby("master_metadata_album_artist_name")["minutes_played"]
        .sum()  # .groupby and .sum are used to rank by mins played rather than times played
        .sort_values(ascending=False)
        .head(10)
        .index
    )
    for artist in top_10_artists:
        artist_data = df[df["master_metadata_album_artist_name"] == artist]
        plays = len(artist_data)
        minutes = artist_data["minutes_played"].sum()
        file_handle.write(
            f"  • {artist}: {minutes:,.0f} min ({minutes / 60:.1f} hrs) | {plays:,} plays\n"
        )

    # Top 10 Songs
    file_handle.write("\nTop 10 Songs (by Minutes Listened):\n")
    top_10_songs = (
        df.groupby("master_metadata_track_name")["minutes_played"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
        .index
    )
    for song in top_10_songs:
        song_data = df[df["master_metadata_track_name"] == song]
        # Since we rank by time, it makes sense to put time first in the output
        minutes = song_data["minutes_played"].sum()

        primary_artist_series = song_data.groupby("master_metadata_album_artist_name")[
            "minutes_played"
        ].sum()
        artist = (
            primary_artist_series.idxmax()
            if not primary_artist_series.empty
            else "Unknown"
        )

        plays = len(song_data)

        file_handle.write(
            f"  • '{song}' by {artist}: {minutes:,.0f} min ({minutes / 60:.1f} hrs) | {plays:,} plays\n"
        )

    # Top 10 Albums
    file_handle.write("\nTop 10 Albums (by Minutes Listened):\n")
    top_10_albums = (
        df.groupby("master_metadata_album_album_name")["minutes_played"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
        .index
    )
    for album in top_10_albums:
        album_data = df[df["master_metadata_album_album_name"] == album]
        minutes = album_data["minutes_played"].sum()

        primary_artist_series = album_data.groupby("master_metadata_album_artist_name")[
            "minutes_played"
        ].sum()
        artist = (
            primary_artist_series.idxmax()
            if not primary_artist_series.empty
            else "Unknown"
        )

        plays = len(album_data)

        file_handle.write(
            f"  • '{album}' by {artist}: {minutes:,.0f} min ({minutes / 60:.1f} hrs) | {plays:,} plays\n"
        )


output_file_name = "listening_stats_summary.txt"

with open(output_file_name, "w", encoding="utf-8") as f:
    # Call 1: overall stats
    write_summary_stats(df_clean, f)

    # Call 2: yearly stats
    for y in sorted(
        df_clean["year"].unique(), reverse=True
    ):  # reverse=True to make the latest year appear first
        write_summary_stats(df_clean, f, year=y)


"""
Visualization Execution Block
- This section calls the bar chart and line chart functions and passes the filename to the functions
- Actually produces the visualizations
"""

# collection of 3 dictionaries that can be used in bar chart calls (reduces repetition!! yay!!)
bar_chart_categories = [
    {
        "col": "master_metadata_album_artist_name",
        "label": "Artists",
        "include_artist": False,
    },
    {"col": "master_metadata_track_name", "label": "Songs", "include_artist": True},
    {
        "col": "master_metadata_album_album_name",
        "label": "Albums",
        "include_artist": True,
    },
]

# 1. Yearly Listening Bar Charts
for y in sorted(df_clean["year"].unique()):
    df_year = filter_year(df_clean, y)
    for cat in bar_chart_categories:
        title = f"Top {cat['label']} of {y}"
        filename = f"Top_{cat['label']}_of_{y}.png"
        bar_chart(
            df_year, cat["col"], title, filename, include_artist=cat["include_artist"]
        )

# 2. All Time Listening Bar Charts
for cat in bar_chart_categories:
    title = f"Top {cat['label']} (All Time)"
    filename = f"All_Time_Top_{cat['label']}.png"
    bar_chart(
        df_clean, cat["col"], title, filename, include_artist=cat["include_artist"]
    )

# 3. Line Chart by Month (All Time)
line_chart(
    df_clean,
    "year_month",
    "Listening Data By Month (All Time)",
    "Month",
    "All_Time_Listening_By_Month.png",
    show_every_nth=6,
    figsize=(14, 7),
)

# 4. Line Chart by Year (All Time)
line_chart(
    df_clean,
    "year",
    "Listening Data By Year (All Time)",
    "Year",
    "All_Time_Listening_By_Year.png",
    figsize=(10, 6),
)

print("\nAll visualization figures have been saved to your directory.")

#################################################################################################################################
# Extra Credit 

"""
Streamgraphs!
- Generates Streamgraphs for both Minutes Played and Play Count (Plays)
- Includes Raw, STL Trend, and Rolling Mean smoothing for each metric.
"""

CUSTOM_PALETTE = (
    "#9e0142",
    "#d53e4f",
    "#f46d43",
    "#fdae61",
    "#fee08b",
    "#e6f598",
    "#abdda4",
    "#66c2a5",
    "#3288bd",
    "#5e4fa2",
)


def generate_streamgraphs(
    df, column_name, metric_label, filename_prefix, item_count=10, seasonal_period=12
):
    print(f"\nProcessing Streamgraphs for: {metric_label}")

    # 1. Aggregation and Sorting (Common for both Minutes and Counts)
    top_items_list = (
        df.groupby(column_name)["minutes_played"]
        .sum()
        .sort_values(ascending=False)
        .head(item_count)
        .index.tolist()
    )

    df_top = df[df[column_name].isin(top_items_list)].copy()

    # --- Centralized Plotting Helper Function ---
    def _plot_single_streamgraph(
        df_plot,
        item_type,
        smoothing_title,
        smoothing_abbr,
        file_unit_suffix,
        unit_name,
        offset_type="sym",
    ):
        df_plot = df_plot.dropna()

        if df_plot.empty or df_plot.sum().sum() == 0:
            print(
                f"Skipped {item_type}_{file_unit_suffix}_{smoothing_abbr}_Streamgraph.png: Not enough valid data."
            )
            return

        time_series = df_plot.index
        y_data = df_plot.T.values
        labels = df_plot.columns.tolist()

        plt.figure(figsize=(16, 9))

        palette = CUSTOM_PALETTE[: len(labels)]

        plt.stackplot(
            time_series,
            y_data,
            labels=labels,
            colors=palette,
            edgecolor="none",
            baseline=offset_type,
        )

        # Add a central axis line for the symmetric plot (the y=0 line)
        if offset_type == "sym":
            plt.axhline(0, color="gray", linestyle="--", linewidth=0.7, alpha=0.7)

        # Build Title and Y-Axis Label (Updated for new naming convention)

        # Title construction: Item Type | Metric Type | Smoothing Type Streamgraph
        base_title = f"{item_type} | {unit_name} | {smoothing_title} Streamgraph"

        y_label = f"Monthly {unit_name}"
        if offset_type == "sym":
            y_label += " (Symmetric Baseline)"

        plt.title(
            base_title,
            fontsize=16,
            fontfamily="monospace",
            pad=20,
        )
        plt.ylabel(y_label, fontsize=12)

        ax = plt.gca()
        ax.xaxis.set_major_locator(mdates.YearLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

        plt.legend(
            loc="upper left",
            bbox_to_anchor=(1.01, 1),
            fontsize=10,
            title=f"Top {item_count} {item_type}s",
        )

        plt.margins(0, 0.05)
        plt.grid(False, axis="y")  # Remove horizontal grid lines
        plt.tight_layout()

        filename_item = item_type.replace(" ", "_")
        filename_metric = file_unit_suffix
        filename_smooth = smoothing_abbr

        filename = (
            f"{filename_item}_{filename_metric}_{filename_smooth}_Streamgraph.png"
        )

        plt.savefig(filename, bbox_inches="tight")
        plt.close()
        print(f"Generated {filename}")

    # Calculate monthly minutes played
    monthly_minutes_data = (
        df_top.groupby([column_name, pd.Grouper(key="ts", freq="ME")])["minutes_played"]
        .sum()
        .reset_index(name="minutes")
    )
    monthly_series_df_minutes = monthly_minutes_data.pivot(
        index="ts", columns=column_name, values="minutes"
    ).fillna(0)[top_items_list]  # Apply column sorting

    # Calculate monthly play count
    monthly_plays_data = (
        df_top.groupby([column_name, pd.Grouper(key="ts", freq="ME")])["ts"]
        .size()  # Count the number of streams
        .reset_index(name="plays")
    )
    monthly_series_df_plays = monthly_plays_data.pivot(
        index="ts", columns=column_name, values="plays"
    ).fillna(0)[top_items_list]  # Apply column sorting

    def apply_smoothing(
        df_in, seasonal_period, window_size=6
    ):  # smoothing logic function
        # Calculate STL Trend component
        trend_df_stl = pd.DataFrame(index=df_in.index)

        for item in df_in.columns:
            ts_item = df_in[item]

            if len(ts_item) < seasonal_period * 2:
                trend_df_stl[item] = ts_item
                continue

            try:
                decomposition = seasonal_decompose(
                    ts_item,
                    model="additive",
                    period=seasonal_period,
                    extrapolate_trend="freq",
                )
                trend_df_stl[item] = decomposition.trend
            except Exception:
                trend_df_stl[item] = ts_item.rolling(
                    window=seasonal_period, center=True
                ).mean()

        # Calculate Rolling Mean component
        trend_df_roll = df_in.rolling(
            window=window_size, center=True, min_periods=1
        ).mean()

        return df_in, trend_df_stl, trend_df_roll

    # Define plot types for iteration: (Display Title Name, File Name Abbreviation)
    plot_variants = [
        ("Raw Data", "Raw"),
        ("STL Trend", "STL"),
        ("6-Month Rolling Mean", "Rolling"),
    ]

    # Iterate over the two metrics (Minutes and Plays)
    for df_raw_metric, unit_name, file_unit_suffix in [
        (monthly_series_df_minutes, "Minutes Played", "Minutes"),
        (monthly_series_df_plays, "Plays", "Plays"),
    ]:
        # Apply smoothing to the current metric data
        df_raw, df_stl, df_roll = apply_smoothing(df_raw_metric, seasonal_period)

        # Define dataframes for iteration: (DataFrame, Display Title Name, File Name Abbreviation)
        data_sets = [
            (df_raw, plot_variants[0][0], plot_variants[0][1]),
            (df_stl, plot_variants[1][0], plot_variants[1][1]),
            (df_roll, plot_variants[2][0], plot_variants[2][1]),
        ]

        # Iterate over the three plot types
        for df_data, smoothing_title, smoothing_abbr in data_sets:
            # Pass the item type, smoothing type, file unit, and display unit
            _plot_single_streamgraph(
                df_data,
                metric_label,
                smoothing_title,
                smoothing_abbr,
                file_unit_suffix,
                unit_name,
                offset_type="sym",
            )

# Call the new streamgraph function for all three categories, now generating 6 plots each
generate_streamgraphs(
    df_clean, "master_metadata_album_artist_name", "Artist", "Artist_Evolution"
)

generate_streamgraphs(
    df_clean, "master_metadata_album_album_name", "Album", "Album_Evolution"
)

generate_streamgraphs(df_clean, "master_metadata_track_name", "Song", "Song_Evolution")


# # All-time bar charts remain the same
# bar_chart_categories = [
#     {
#         "col": "master_metadata_album_artist_name",
#         "label": "Artists",
#         "include_artist": False,
#     },
#     {"col": "master_metadata_track_name", "label": "Songs", "include_artist": True},
#     {
#         "col": "master_metadata_album_album_name",
#         "label": "Albums",
#         "include_artist": True,
#     },
# ]

# for cat in bar_chart_categories:
#     title = f"Top {cat['label']} (All Time)"
#     filename = f"All_Time_Top_{cat['label']}.png"
#     bar_chart(
#         df_clean, cat["col"], title, filename, include_artist=cat["include_artist"]
#     )

# # 3. Line Chart by Month (All Time)
# line_chart(
#     df_clean,
#     "year_month",
#     "Listening Data By Month (All Time)",
#     "Month",
#     "All_Time_Listening_By_Month.png",
#     show_every_nth=6,
#     figsize=(14, 7),
# )

# # 4. Line Chart by Year (All Time)
# line_chart(
#     df_clean,
#     "year",
#     "Listening Data By Year (All Time)",
#     "Year",
#     "All_Time_Listening_By_Year.png",
#     figsize=(10, 6),
# )
