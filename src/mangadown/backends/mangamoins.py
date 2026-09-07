"""Backend for https://mangamoins.com.

The site is a JS front end over a small JSON API.  Two quirks shape this
backend:

* The API only answers a session that has already loaded the corresponding
  HTML page, so each call is preceded by a request to that page.
* ``pagesBaseUrl`` comes back padded with two filler substrings that the
  site's own reader strips client-side before requesting images.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

from curl_cffi import Session

from mangadown.cache import Cache
from mangadown.downloader import download_images

log = logging.getLogger(__name__)

_BASE_URL = "https://mangamoins.com"
_TIMEOUT = 30
_MAX_CATALOGUE_PAGES = 20

# Filler injected into pagesBaseUrl by the server and removed by the site's
# reader (reader.js: this.oreiller / this.polochon) before it requests a page.
# These are literals in that file, so they can change on any deploy; if every
# page starts 404ing, re-read them there.
_URL_FILLER = ("bztmrkeiyoushi", "_b")

_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
)


class MangaMoins:
    """Scraper for mangamoins.com."""

    def __init__(self) -> None:
        self._session = Session(impersonate="chrome", timeout=_TIMEOUT)

    @property
    def name(self) -> str:
        return "mangamoins"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_mangas(self, cache: Cache) -> dict[str, str]:
        """Return ``{title: relative_url}`` for the whole catalogue.

        Results are cached in *cache* under the ``"mangas"`` key.
        """
        cached = cache.get("mangas")
        if cached is not None:
            return cached

        mangas: dict[str, str] = {}
        rows = 0
        for page_num in range(1, _MAX_CATALOGUE_PAGES + 1):
            payload = self._api("/", "/api/v1/mangas", page=page_num)
            entries = payload.get("data") or []
            if not entries:
                break

            for entry in entries:
                slug = entry.get("mangaSlug")
                if not slug:
                    continue
                mangas.setdefault(self._title(slug), f"/manga/{slug}")

            # The catalogue is keyed by recent chapter, not by series, so one
            # series repeats across rows; count rows rather than titles or the
            # loop never reaches `total`.
            rows += len(entries)
            total, limit = payload.get("total"), payload.get("limit")
            if isinstance(total, int) and rows >= total:
                break
            if isinstance(limit, int) and len(entries) < limit:
                break

        log.info("Found %d manga on mangamoins", len(mangas))
        cache.set("mangas", mangas)
        return mangas

    def get_chapters(self, manga_url: str) -> dict[float, str]:
        """Return ``{chapter_number: chapter_url}`` for a manga."""
        slug = self._slug(manga_url, "manga")
        payload = self._api(f"/manga/{slug}", "/api/v1/manga", manga=slug)

        chapters: dict[float, str] = {}
        for chapter in payload.get("chapters") or []:
            num, chapter_slug = chapter.get("num"), chapter.get("slug")
            if num is None or not chapter_slug:
                continue
            try:
                chapters[float(num)] = f"/scan/{chapter_slug}"
            except (TypeError, ValueError):
                continue
        return chapters

    async def download_chapter(self, chapter_url: str, dest: Path) -> None:
        """Download all page images for a chapter into *dest*."""
        slug = self._slug(chapter_url, "scan")
        page_path = f"/scan/{slug}"
        payload = self._api(page_path, "/api/v1/scan", slug=slug)

        base = payload.get("pagesBaseUrl")
        count = payload.get("pageNumbers")
        if not base or not isinstance(count, int) or count < 1:
            raise RuntimeError(f"No pages listed for mangamoins chapter {slug}")

        for filler in _URL_FILLER:
            base = base.replace(filler, "")

        # Source pages are two-digit; destination names are padded to match the
        # width the converter expects for reading order.
        width = max(3, len(str(count)))
        urls = {f"{idx:0{width}d}.webp": f"{base}{idx:02d}.webp" for idx in range(1, count + 1)}

        await download_images(
            urls,
            dest,
            headers={"User-Agent": _USER_AGENT, "Referer": _BASE_URL + page_path},
            cookies=dict(self._session.cookies),
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _api(self, page_path: str, endpoint: str, **params: Any) -> dict[str, Any]:
        """Load *page_path* to authorise the session, then GET *endpoint*.

        Query parameters go through ``params``, so this signature deliberately
        avoids names the API itself uses (``page``, ``slug``, ``manga``).
        """
        self._session.get(_BASE_URL + page_path)
        resp = self._session.get(
            _BASE_URL + endpoint,
            params=params,
            headers={"Accept": "application/json", "Referer": _BASE_URL + page_path},
        )
        if resp.status_code != 200:
            raise RuntimeError(f"mangamoins {endpoint} returned {resp.status_code}")

        payload = resp.json()
        if not isinstance(payload, dict):
            raise RuntimeError(f"mangamoins {endpoint} returned {type(payload).__name__}")
        if payload.get("error"):
            raise RuntimeError(f"mangamoins {endpoint}: {payload['error']}")
        return payload

    @staticmethod
    def _slug(path_or_url: str, kind: str) -> str:
        """Extract the slug from a ``/<kind>/<slug>`` path."""
        m = re.search(rf"/{kind}/([^/?#]+)", path_or_url)
        if not m:
            raise RuntimeError(f"Not a mangamoins {kind} url: {path_or_url}")
        return m.group(1)

    @staticmethod
    def _title(manga_slug: str) -> str:
        """Normalise a slug to the shared title key (``one_piece`` -> ``one piece``)."""
        return manga_slug.replace("_", " ").replace("-", " ").lower()
