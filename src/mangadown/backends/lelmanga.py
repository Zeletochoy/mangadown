"""Backend for https://www.lelmanga.com."""

from __future__ import annotations

import logging
import re
from itertools import count
from pathlib import Path
from urllib.parse import urlsplit

from bs4 import BeautifulSoup, Tag
from curl_cffi import Session

from mangadown.cache import Cache
from mangadown.downloader import download_images

log = logging.getLogger(__name__)

_BASE_URL = "https://www.lelmanga.com"
_TIMEOUT = 30

# curl_cffi impersonates a browser at the TLS layer rather than through a headers
# dict, so Session.headers is empty and the image downloader needs its own UA.
_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
)


def _attr(tag: Tag, name: str) -> str:
    """Return a tag attribute as a single string.

    BeautifulSoup types attributes as ``str | list[str]`` because HTML allows
    multi-valued ones, and neither ``.strip()`` nor ``float()`` accepts a list.
    """
    value = tag.get(name)
    if isinstance(value, str):
        return value
    if isinstance(value, list) and value:
        return str(value[0])
    return ""


class LelManga:
    """Scraper for lelmanga.com."""

    def __init__(self) -> None:
        self._session = Session(impersonate="chrome", timeout=_TIMEOUT)

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
                href = _attr(a, "href").strip().rstrip("/")
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
                num = float(_attr(li, "data-num"))
            except (ValueError, KeyError):
                continue
            a = li.find("a", href=True)
            if not a:
                continue
            chapters[num] = _attr(a, "href").strip()

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
            if not isinstance(img_url, str) or "wp-content/uploads" not in img_url:
                continue
            # URLs are served through the CDN with a cache-busting query string
            # (".../001.webp?lmv=123"), so match the extension on the path only.
            fname = urlsplit(img_url).path.rsplit("/", 1)[-1]
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
            headers={"User-Agent": _USER_AGENT},
            cookies=dict(self._session.cookies),
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
