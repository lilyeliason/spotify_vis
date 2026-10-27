# spotify-viz

A series of data visualizations for my Spotify listening data.

It turns a Spotify Extended Streaming History export into a text summary and a
set of charts: top artists, songs, and albums (all time and per year), plays
over time, and streamgraphs of how top artists, songs, and albums change month
to month.

The repo includes my listening history from 2017 to 2025 as a sanitized
Parquet file, so cloning it and running the pipeline reproduces my charts. The
generated charts and summary are committed in `outputs/`.

## Install

Requires Python 3.10 or newer. With [uv](https://docs.astral.sh/uv/):

```sh
uv sync
```

Or with pip:

```sh
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

### Fonts (optional)

Charts use Inter if it is available. Download it from
[rsms.me/inter](https://rsms.me/inter/) (or the
[GitHub releases](https://github.com/rsms/inter/releases)), unzip, and copy
the static files from `extras/ttf/` (at least `Inter-Regular.ttf`,
`Inter-Medium.ttf`, and `Inter-SemiBold.ttf`) into `fonts/`. Use the static
files rather than the variable font, which matplotlib does not handle well.
If `fonts/` is empty, charts fall back to Helvetica Neue, Helvetica, or Arial.

## Run

```sh
uv run python scripts/run_all.py
```

With `data/raw/` empty, this reads `data/clean/listening_history.parquet`.
If raw export files are in `data/raw/`, it uses those instead and rewrites the
sanitized file whenever it re-parses them.

Options:

- `--refresh` re-parses the raw JSON in `data/raw/`. Otherwise the parsed data
  is cached in `data/processed/` and only rebuilt when the raw files change.
- `--years 2023 2024` limits the per-year charts to those years.

Outputs go to `outputs/figures/` and `outputs/summaries/`.

Settings such as the timezone, the minimum play length, and the number of top
items are in `src/spotify_viz/config.py`.

## Using your own data

1. Go to your Spotify account's [Privacy settings](https://www.spotify.com/account/privacy/).
2. Under "Download your data", select **Extended streaming history** and request it.
3. Spotify emails a download link, usually within a few days (it can take up to 30).
4. Unzip it, copy the `Streaming_History_Audio_*.json` files into `data/raw/`,
   and run with `--refresh`. The video history file is ignored.

This replaces `data/clean/listening_history.parquet` and `outputs/` with your
data, so don't commit those unless you mean to publish your history.

## How things are counted

- Timestamps are converted from UTC to the timezone in `config.py`
  (default `America/Denver`) before dates, hours, and years are derived.
- A **play** is a stream of at least 30 seconds. **Minutes listened** includes
  every stream, skips too. Rankings use minutes listened.
- Songs are grouped by track name plus primary artist, and albums by album name
  plus primary artist. This merges a single and its album version into one
  song, while two different songs that share a title stay separate. The
  Spotify track URI is still kept in the data.
- Podcasts, audiobooks, and other rows without a track name are flagged in the
  `content_type` column and left out of all music charts and totals.

## Privacy

The raw Spotify export includes an IP address and account details. It lives
only in `data/raw/`, which is gitignored, and is never committed. The parsed
cache in `data/processed/` is gitignored too.

`data/clean/listening_history.parquet` is built from an allowlist of columns
(`config.CLEAN_COLUMNS`): timestamps, time played, track, artist, album,
track URI, podcast episode and audiobook names, skipped, shuffle, start and
end reasons, platform, offline, and country. Fields that identify the account
or device session (`ip_addr`, `username`, `user_agent_decrypted`,
`incognito_mode`, `offline_timestamp`) are never written, and any new field in
a future export is left out until it is added to the allowlist.

## Layout

```
src/spotify_viz/   config, loading, metrics, styling, summary, plots/
scripts/           run_all.py (entry point)
data/              clean/ (sanitized history, committed), raw/ and processed/ (ignored)
outputs/           generated figures and summary
docs/images/       curated charts for this README
notebooks/         exploration
```
