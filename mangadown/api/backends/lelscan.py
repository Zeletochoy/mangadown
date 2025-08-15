#! /usr/bin/env python3

# Backend for https://lelscanfr.com – implements get_mangas, get_chapters and
# download_chapter, mirroring the other backends.

from .. import utils

import os
import re
from itertools import count

import cloudscraper
from bs4 import BeautifulSoup


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

BASE_URL = "https://lelscanfr.com"

# A single cloudscraper session for the whole module so that we share cookies
# (useful to bypass Cloudflare challenges only once).
requests = cloudscraper.create_scraper(allow_brotli=False)


# ---------------------------------------------------------------------------
# Public API expected by mangadown
# ---------------------------------------------------------------------------


@utils.json_cached("lelscanfr.json")
def get_mangas():
    """Return a mapping {title (str, lower): url (str)} for all mangas.

    The public directory is paginated (`/manga?page=N`). We iterate until we do
    not discover any new mangas.  Each manga is exposed as an <a> with an href
    that starts with `/manga/` and is followed by a *slug* (the chapter number
    is *not* present at this stage).  We derive a readable title from the slug
    by replacing the dash by space and lower-casing – this is consistent with
    the behaviour of the existing backends.
    """

    print("Fetching manga list from lelscanfr: page ", end="", flush=True)

    mangas = {}

    size_before = 0
    for page_num in count(1):
        print(f"{page_num}, ", end="", flush=True)
        url = f"{BASE_URL}/manga?page={page_num}"
        resp = requests.get(url)

        # Stop if we hit a non-success HTTP status (network / pagination end)
        if resp.status_code != 200:
            break

        soup = BeautifulSoup(resp.text, "html.parser")

        # Collect all anchors that reference a manga page (but *not* a chapter
        # page which would have an additional path component with digits).
        page_links_found = False
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()

            if not href.startswith("/manga/") and not href.startswith(BASE_URL + "/manga/"):
                continue

            # Keep only links that have exactly one extra component after
            # `/manga/`, i.e. the slug of the series.
            after = href.split("/manga/")[-1].split("?")[0].strip("/")
            if after == "" or "/" in after or after.isdigit():
                continue  # chapter page or invalid

            # Normalize URL (we store a relative path so that the backend keeps
            # the same style as the others).
            rel_url = "/manga/" + after

            # Derive title – we follow the convention of other backends:
            #   lowercase, plain string (spaces instead of dashes)
            title = after.replace("-", " ").lower()

            # Add only if not already present.
            if title not in mangas:
                mangas[title] = rel_url
            page_links_found = True

        # Stop when either no manga links were found **or** the size of the
        # dictionary did not change (meaning we've wrapped around).
        if not page_links_found or len(mangas) == size_before:
            break

        size_before = len(mangas)

    print("done")
    return mangas


def _full_url(path_or_url):
    """Return an absolute URL for *path_or_url* (which may already be absolute).
    """
    if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
        return path_or_url
    # Ensure there is a leading slash so that urljoin is not needed.
    if not path_or_url.startswith("/"):
        path_or_url = "/" + path_or_url
    return BASE_URL + path_or_url


def get_chapters(manga_url):
    """Return a mapping {chapter_number (float): chapter_url (str)}."""

    url = _full_url(manga_url)
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, "html.parser")

    chapters = {}

    # The list of chapters is located in the element with id="chapters-list".
    for a in soup.select("#chapters-list a"):
        href = a.get("href")
        if not href:
            continue

        href = href.strip()
        # Normalise relative path.
        full = _full_url(href)

        # Extract numeric part after the last '/'.  The site occasionally uses
        # decimals (e.g. 1053.5) so we convert to float.
        last_part = full.rstrip("/").split("/")[-1]
        try:
            num = float(last_part)
        except ValueError:
            continue

        chapters[num] = full

    return chapters


def download_chapter(chapter_url, path, loop):
    """Download one chapter into *path* then return when finished.

    The chapter page already embeds all individual page images as <img>
    elements.  Each page image has its URL in the `data-src` attribute and is
    hosted under `/storage/content/…`.  We collect those URLs, skip obvious ad
    placeholders and hand the list over to `utils.download_urls` which will
    drive the asynchronous downloads.
    """

    url = _full_url(chapter_url)
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, "html.parser")

    # Collect all image URLs belonging to the manga pages.
    urls = {}
    for img in soup.find_all("img"):
        img_url = img.get("data-src") or img.get("src", "")
        if not img_url:
            continue

        # Only keep images hosted under /storage/content/ — this avoids ads,
        # logos, avatars, …
        if "/storage/content/" not in img_url:
            continue

        # Ignore placeholders without an actual filename.
        fname = img_url.rsplit("/", 1)[-1]
        if not re.search(r"\.(webp|jpg|jpeg|png)$", fname, re.IGNORECASE):
            continue

        urls[fname] = img_url

    # Nothing to download -> abort early.
    if not urls:
        raise RuntimeError("No content images found on chapter page")

    os.makedirs(path, exist_ok=True)
    utils.download_urls(urls, path, loop, headers=requests.headers, cookies=requests.cookies)
