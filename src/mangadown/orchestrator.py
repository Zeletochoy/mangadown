"""Core workflow: check MAL progress, download new chapters, convert to EPUB."""

from __future__ import annotations

import asyncio
import logging
import shutil
from collections import defaultdict
from pathlib import Path

from mangadown.backends import Backend
from mangadown.cache import Cache
from mangadown.config import Settings
from mangadown.converter import dir_to_epub
from mangadown.mal import get_reading_list, resolve_mal_title

log = logging.getLogger(__name__)


def _build_manga_index(
    backends: list[Backend],
    cache_dir: Path,
    *,
    use_cache: bool = True,
) -> dict[str, list[tuple[Backend, str]]]:
    """Return ``{title: [(backend, url), ...]}`` across all backends."""
    index: dict[str, list[tuple[Backend, str]]] = defaultdict(list)
    for backend in backends:
        cache = Cache(cache_dir, backend.name)
        if not use_cache:
            cache.clear()
        mangas = backend.get_mangas(cache)
        for title, url in mangas.items():
            index[title].append((backend, url))
    return index


def list_mangas(
    backends: list[Backend], settings: Settings, *, use_cache: bool = True
) -> list[str]:
    """Return sorted list of all available manga titles."""
    index = _build_manga_index(backends, settings.cache_dir, use_cache=use_cache)
    return sorted(index.keys())


def run_updates(
    mangas: list[str],
    backends: list[Backend],
    settings: Settings,
    *,
    use_cache: bool = True,
    chooser: callable | None = None,
) -> None:
    """Download new chapters for each manga in *mangas*.

    For each manga:
    1. Find it across backends
    2. Get chapter list
    3. Compare with MAL reading progress
    4. Download + convert new chapters to EPUB
    """
    settings.ensure_dirs()

    index = _build_manga_index(backends, settings.cache_dir, use_cache=use_cache)

    # Fetch MAL progress once.
    progress: dict[str, int] = {}
    if settings.mal_user:
        mal_cache = Cache(settings.cache_dir, "mal")
        mal_entries = get_reading_list(settings.mal_user)
        progress = {e.title: e.chapters_read for e in mal_entries}

    for manga_title in mangas:
        if manga_title not in index:
            log.warning("Manga not found: %s", manga_title)
            continue

        log.info("Updating %s", manga_title)

        # Gather chapters from all backends that have this manga.
        chapters: dict[float, list[tuple[Backend, str]]] = defaultdict(list)
        for backend, manga_url in index[manga_title]:
            try:
                backend_chapters = backend.get_chapters(manga_url)
            except Exception:
                log.warning("%s.get_chapters(%s) failed", backend.name, manga_title, exc_info=True)
                continue
            for num, url in backend_chapters.items():
                chapters[num].append((backend, url))

        if not chapters:
            log.info("  No chapters available")
            continue

        # Determine which chapters to download based on MAL progress.
        current = 0
        if settings.mal_user:
            mal_cache = Cache(settings.cache_dir, "mal")
            mal_title = resolve_mal_title(manga_title, mal_cache, chooser=chooser)
            if mal_title:
                current = progress.get(mal_title, 0)

        latest = max(chapters)
        log.info("  Progress: %d/%s", current, f"{latest:g}")

        for chap_num in sorted(chapters):
            if chap_num <= current:
                continue

            chap_label = f"{chap_num:g}"
            folder_name = f"{manga_title} {chap_label}"
            epub_path = settings.output_dir / f"{folder_name}.epub"

            # Skip already-downloaded chapters.
            if epub_path.exists():
                continue

            tmp_dir = settings.output_dir / folder_name
            tmp_epub = settings.output_dir / f"{folder_name}.epub.tmp"

            # Try each backend until one succeeds.
            downloaded = False
            for backend, chapter_url in chapters[chap_num]:
                try:
                    log.info("  Downloading chapter %s from %s", chap_label, backend.name)
                    asyncio.run(backend.download_chapter(chapter_url, tmp_dir))
                    downloaded = True
                    break
                except Exception:
                    log.warning(
                        "  %s.download_chapter(%s, %s) failed",
                        backend.name,
                        manga_title,
                        chap_label,
                        exc_info=True,
                    )
                    if tmp_dir.is_dir():
                        shutil.rmtree(tmp_dir)

            if not downloaded:
                log.warning("  Failed to download chapter %s", chap_label)
                continue

            # Convert to EPUB (atomic: write .tmp, then rename).
            try:
                result = dir_to_epub(tmp_dir, settings.output_dir)
                # KCC writes directly to output_dir; rename for atomicity.
                result.rename(tmp_epub)
                tmp_epub.rename(epub_path)
                log.info("  Chapter %s done", chap_label)
            except Exception:
                log.warning("  Conversion failed for chapter %s", chap_label, exc_info=True)
                if tmp_epub.exists():
                    tmp_epub.unlink()
            finally:
                if tmp_dir.is_dir():
                    shutil.rmtree(tmp_dir)

        log.info("  %s complete", manga_title)
