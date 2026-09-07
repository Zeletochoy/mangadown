# mangadown

Automated manga downloader for Kindle. Scrapes manga chapters from web sources, converts them to EPUB, tracks reading progress via MyAnimeList, and delivers EPUBs to Kindle via email.

## Setup

Requires Python 3.12+.

```bash
uv pip install -e ".[dev]"
```

## Configuration

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Required environment variables:

| Variable | Description |
|---|---|
| `MANGADOWN_MAL_USER` | MyAnimeList username |
| `MANGADOWN_GMAIL_USER` | Gmail address for delivery |
| `MANGADOWN_GMAIL_PASSWORD` | Gmail app password |
| `MANGADOWN_KINDLE_EMAIL` | Kindle email address |

Optional overrides for data paths (defaults to XDG directories):

| Variable | Description |
|---|---|
| `MANGADOWN_CACHE_DIR` | Cache directory |
| `MANGADOWN_OUTPUT_DIR` | EPUB output directory |
| `MANGADOWN_TRACKED_FILE` | Path to tracked manga list |

## Usage

### Download new chapters

```bash
# Download chapters for tracked manga
mangadown download

# Download specific manga
mangadown download "one piece" "dragon ball super"

# List available manga
mangadown download --list

# Show MAL reading progress
mangadown download --list-mal

# Force refresh (ignore cache)
mangadown download --no-cache

# Verbose: per-request HTTP logs and full tracebacks on failures
mangadown download -v
```

## Sources

Chapters are fetched from the backends in `mangadown.backends.get_backends()`,
in order:

| Backend | Notes |
|---|---|
| `lelmanga` | Primary. Plain HTML pages. |
| `mangamoins` | Fallback. JSON API; smaller catalogue. |

Each chapter is tried against every backend that carries the manga until one
succeeds, so a chapter missing from the primary source is picked up from the
fallback. Backends key manga by a normalised title (`one-piece` and `one_piece`
both become `one piece`), which is what lets them substitute for one another —
a new backend must normalise the same way.

If every backend fails for a chapter, it is reported as a single warning and
skipped. It is not marked as downloaded, so a later run retries it.

An unreachable source degrades rather than aborting: if a backend's catalogue
cannot be fetched, it is logged and the remaining backends still run.

### Send EPUBs to Kindle

```bash
# Send all EPUBs in output directory
mangadown send

# Send specific files
mangadown send path/to/file.epub
```

## Tracked file

Create a text file (default: `$XDG_DATA_HOME/mangadown/tracked`) with one manga title per line. Lines starting with `#` are comments.

```
one piece
one punch man
dragon ball super
# d gray man
```

## Development

```bash
uv pip install -e ".[dev]"
uv run pytest
uv run ruff check src/ tests/
uv run ruff format src/ tests/
```
