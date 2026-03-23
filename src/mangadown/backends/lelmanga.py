"""Backend for https://www.lelmanga.com."""

from __future__ import annotations

import logging
import re
from itertools import count
from pathlib import Path

import cloudscraper
from bs4 import BeautifulSoup

from mangadown.cache import Cache
from mangadown.downloader import download_images

log = logging.getLogger(__name__)

_BASE_URL = "https://www.lelmanga.com"


class LelManga:
    """Scraper for lelmanga.com."""

    def __init__(self) -> None:
        self._session = cloudscraper.create_scraper(allow_brotli=False)

    @property
    def name(self) -> str:
        return "lelmanga"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_mangas(self, cache: Cache) -> dict[str, str]:
        """Return ``{title: relative_url}`` for all manga on the site.

        Results are cached in *cache* under the ``"mangas"`` key.
        """
        cached = cache.get("mangas")
        if cached is not None:
            return cached

        log.info("Fetching manga list from lelmanga: page ")
        mangas: dict[str, str] = {}

        size_before = 0
        for page_num in count(1):
            log.info("  page %d", page_num)
            resp = self._session.get(f"{_BASE_URL}/manga/?page={page_num}")
            if resp.status_code != 200:
                break

            soup = BeautifulSoup(resp.text, "html.parser")
            for a in soup.find_all("a", href=True):
                href = a["href"].strip().rstrip("/")
                m = re.match(rf"^(?:{re.escape(_BASE_URL)})?/manga/([a-z0-9][\w-]*)$", href)
                if not m:
                    continue
                slug = m.group(1)
                if slug in ("page", "feed"):
                    continue
                title = slug.replace("-", " ").lower()
                if title not in mangas:
                    mangas[title] = f"/manga/{slug}"

            if len(mangas) == size_before:
                break
            size_before = len(mangas)

        log.info("Found %d manga", len(mangas))
        cache.set("mangas", mangas)
        return mangas

    def get_chapters(self, manga_url: str) -> dict[float, str]:
        """Return ``{chapter_number: chapter_url}`` for a manga page."""
        url = self._full_url(manga_url)
        resp = self._session.get(url)
        soup = BeautifulSoup(resp.text, "html.parser")

        chapters: dict[float, str] = {}
        chapter_list = soup.find(id="chapterlist")
        if not chapter_list:
            return chapters

        for li in chapter_list.find_all("li", attrs={"data-num": True}):
            try:
                num = float(li["data-num"])
            except (ValueError, KeyError):
                continue
            a = li.find("a", href=True)
            if not a:
                continue
            chapters[num] = a["href"].strip()

        return chapters

    async def download_chapter(self, chapter_url: str, dest: Path) -> None:
        """Download all page images for a chapter into *dest*."""
        url = self._full_url(chapter_url)
        resp = self._session.get(url)
        soup = BeautifulSoup(resp.text, "html.parser")

        reader = soup.find(id="readerarea")
        if not reader:
            raise RuntimeError(f"No #readerarea found on {url}")

        page_imgs: list[tuple[str, str]] = []
        for img in reader.find_all("img"):
            img_url = img.get("data-src") or img.get("src", "")
            if not img_url or "wp-content/uploads" not in img_url:
                continue
            fname = img_url.rsplit("/", 1)[-1]
            m = re.search(r"\.(webp|jpg|jpeg|png)$", fname, re.IGNORECASE)
            if not m:
                continue
            page_imgs.append((img_url, m.group(0).lower()))

        if not page_imgs:
            raise RuntimeError(f"No content images found on {url}")

        # Sequential filenames for reading order.
        width = max(3, len(str(len(page_imgs))))
        urls = {
            f"{idx:0{width}d}{ext}": img_url
            for idx, (img_url, ext) in enumerate(page_imgs, start=1)
        }

        await download_images(
            urls,
            dest,
            headers=dict(self._session.headers),
            cookies={c.name: c.value for c in self._session.cookies},
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _full_url(path_or_url: str) -> str:
        if path_or_url.startswith(("http://", "https://")):
            return path_or_url
        if not path_or_url.startswith("/"):
            path_or_url = "/" + path_or_url
        return _BASE_URL + path_or_url
