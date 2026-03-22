#! /usr/bin/env python3

# Backend for https://www.lelmanga.com – implements get_mangas, get_chapters and
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

BASE_URL = "https://www.lelmanga.com"

# A single cloudscraper session for the whole module so that we share cookies
# (useful to bypass Cloudflare challenges only once).
requests = cloudscraper.create_scraper(allow_brotli=False)


# ---------------------------------------------------------------------------
# Public API expected by mangadown
# ---------------------------------------------------------------------------


@utils.json_cached("lelmanga.json")
def get_mangas():
    """Return a mapping {title (str, lower): url (str)} for all mangas.

    The manga directory is paginated (`/manga/?page=N`).  We iterate until no
    new mangas are discovered.  Each manga is exposed as an <a> with an href
    of the form `https://www.lelmanga.com/manga/<slug>`.  We derive a readable
    title from the slug by replacing dashes with spaces and lower-casing.
    """

    print("Fetching manga list from lelmanga: page ", end="", flush=True)

    mangas = {}

    size_before = 0
    for page_num in count(1):
        print(f"{page_num}, ", end="", flush=True)
        url = f"{BASE_URL}/manga/?page={page_num}"
        resp = requests.get(url)

        if resp.status_code != 200:
            break

        soup = BeautifulSoup(resp.text, "html.parser")

        for a in soup.find_all("a", href=True):
            href = a["href"].strip().rstrip("/")

            # Match links like https://www.lelmanga.com/manga/<slug>
            m = re.match(
                rf"^(?:{re.escape(BASE_URL)})?/manga/([a-z0-9][\w-]*)$", href
            )
            if not m:
                continue

            slug = m.group(1)
            # Skip pagination or feed links
            if slug in ("page", "feed"):
                continue

            title = slug.replace("-", " ").lower()
            rel_url = f"/manga/{slug}"

            if title not in mangas:
                mangas[title] = rel_url

        if len(mangas) == size_before:
            break

        size_before = len(mangas)

    print("done")
    return mangas


def _full_url(path_or_url):
    """Return an absolute URL for *path_or_url* (which may already be absolute)."""
    if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
        return path_or_url
    if not path_or_url.startswith("/"):
        path_or_url = "/" + path_or_url
    return BASE_URL + path_or_url


def get_chapters(manga_url):
    """Return a mapping {chapter_number (float): chapter_url (str)}.

    The chapter list is inside a ``<div id="chapterlist">`` element.  Each
    ``<li>`` carries a ``data-num`` attribute with the chapter number.
    """

    url = _full_url(manga_url)
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, "html.parser")

    chapters = {}

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


def download_chapter(chapter_url, path, loop):
    """Download one chapter into *path* then return when finished.

    The chapter page embeds all page images as ``<img>`` elements inside
    ``<div id="readerarea">``.  Images are hosted under
    ``wp-content/uploads/`` and we filter out logos, ads and thumbnails
    by only keeping images within that reader container.
    """

    url = _full_url(chapter_url)
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, "html.parser")

    reader = soup.find(id="readerarea")
    if not reader:
        raise RuntimeError("No #readerarea found on chapter page")

    page_img_urls = []
    for img in reader.find_all("img"):
        img_url = img.get("data-src") or img.get("src", "")
        if not img_url:
            continue

        # Only keep actual manga page images hosted under wp-content/uploads.
        if "wp-content/uploads" not in img_url:
            continue

        fname = img_url.rsplit("/", 1)[-1]
        m = re.search(r"\.(webp|jpg|jpeg|png)$", fname, re.IGNORECASE)
        if not m:
            continue

        page_img_urls.append((img_url, m.group(0).lower()))

    if not page_img_urls:
        raise RuntimeError("No content images found on chapter page")

    # Build sequential filenames to enforce reading order for KCC.
    width = max(3, len(str(len(page_img_urls))))
    urls = {}
    for idx, (img_url, ext) in enumerate(page_img_urls, start=1):
        fname = f"{idx:0{width}d}{ext}"
        urls[fname] = img_url

    os.makedirs(path, exist_ok=True)
    utils.download_urls(urls, path, loop, headers=requests.headers, cookies=requests.cookies)
