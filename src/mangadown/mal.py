"""MyAnimeList integration via Jikan v4 API."""

from __future__ import annotations

import logging

import httpx

from mangadown.cache import Cache
from mangadown.models import MalProgress

log = logging.getLogger(__name__)

_MAL_LIST_URL = "https://myanimelist.net/mangalist/{user}/load.json"
_MAL_LIST_LIMIT = 300  # MAL returns up to 300 entries per page
_JIKAN_SEARCH_URL = "https://api.jikan.moe/v4/manga"


def get_reading_list(user: str) -> list[MalProgress]:
    """Fetch the user's full manga reading list from MAL.

    Handles pagination (MAL returns 300 entries per page).
    """
    entries: list[MalProgress] = []
    offset = 0

    while True:
        url = _MAL_LIST_URL.format(user=user)
        resp = httpx.get(url, params={"offset": offset, "status": 1})
        resp.raise_for_status()
        page = resp.json()

        if not page:
            break

        for item in page:
            entries.append(
                MalProgress(
                    title=item["manga_title"],
                    chapters_read=item["num_read_chapters"],
                )
            )

        if len(page) < _MAL_LIST_LIMIT:
            break
        offset += _MAL_LIST_LIMIT

    log.info("Fetched %d entries from MAL for user %s", len(entries), user)
    return entries


def search_mal_title(query: str) -> list[str]:
    """Search Jikan v4 for manga titles matching *query*.

    Returns a list of title strings, best matches first.
    """
    resp = httpx.get(_JIKAN_SEARCH_URL, params={"q": query})
    resp.raise_for_status()
    data = resp.json().get("data", [])
    return [item["title"] for item in data]


def resolve_mal_title(
    search: str,
    cache: Cache,
    *,
    chooser: callable | None = None,
) -> str | None:
    """Resolve a manga search string to its canonical MAL title.

    Checks cache first.  If not cached, searches Jikan and:
    - Returns an exact (case-insensitive) match automatically
    - Calls *chooser(candidates)* for disambiguation if provided
    - Returns the first result as fallback

    The result is cached for future lookups.
    """
    cached = cache.get(search)
    if cached is not None:
        return cached

    candidates = search_mal_title(search)
    if not candidates:
        return None

    # Try exact case-insensitive match first.
    title: str | None = None
    for candidate in candidates:
        if search.lower() == candidate.lower():
            title = candidate
            break

    if title is None and chooser is not None:
        title = chooser(candidates[:10])

    if title is None:
        title = candidates[0]

    cache.set(search, title)
    return title
