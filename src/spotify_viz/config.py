"""Project settings. All paths and tunable constants live here."""

from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
CLEAN_FILE = DATA_DIR / "clean" / "listening_history.parquet"
FONTS_DIR = PROJECT_ROOT / "fonts"
FIGURES_DIR = PROJECT_ROOT / "outputs" / "figures"
SUMMARIES_DIR = PROJECT_ROOT / "outputs" / "summaries"

# Only audio history files are loaded; the video history file is ignored.
RAW_FILE_GLOB = "Streaming_History_Audio_*.json"
SUMMARY_FILENAME = "listening_stats_summary.txt"

# Analysis settings
TIMEZONE = "America/Denver"  # Spotify timestamps are UTC; converted to this
MIN_PLAY_MS = 30_000  # a row counts as a "play" only at or above this
TOP_N = 10

# Streamgraph settings
STREAM_ITEM_COUNT = 10
STL_PERIOD = 12  # months
ROLLING_WINDOW = 6  # months

# Fields from the extended history that are removed at load time because
# they identify the user or their device/session.
IDENTIFYING_FIELDS = [
    "ip_addr",
    "ip_addr_decrypted",
    "username",
    "user_agent_decrypted",
    "offline_timestamp",
    "incognito_mode",
]

# The only columns written to the committed sanitized history. This is an
# allowlist, so new fields in a future export are left out until added here.
CLEAN_COLUMNS = [
    "ts",
    "ms_played",
    "minutes_played",
    "master_metadata_track_name",
    "master_metadata_album_artist_name",
    "master_metadata_album_album_name",
    "spotify_track_uri",
    "episode_name",
    "episode_show_name",
    "audiobook_title",
    "audiobook_chapter_title",
    "skipped",
    "shuffle",
    "reason_start",
    "reason_end",
    "platform",
    "offline",
    "conn_country",
    "content_type",
    "is_music",
]

# Column name shortcuts
TRACK = "master_metadata_track_name"
ARTIST = "master_metadata_album_artist_name"
ALBUM = "master_metadata_album_album_name"
