"""Tests for the lelmanga backend's chapter page parsing."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import httpx
import pytest
import respx

from mangadown.backends.lelmanga import LelManga

_CDN = "https://i0.wp.com/www.lelmanga.com/wp-content/uploads/2026/07/some-manga-1"


def _reader_page(body: str) -> str:
    return f'<html><body><div id="readerarea">{body}</div></body></html>'


@dataclass
class FakeResponse:
    text: str
    status_code: int = 200


@dataclass
class FakeSession:
    """Stand-in for the cloudscraper session (the site is the system boundary)."""

    page: str
    headers: dict[str, str] = field(default_factory=dict)
    cookies: tuple[()] = ()

    def get(self, url: str) -> FakeResponse:
        return FakeResponse(self.page)


def _backend(page: str) -> LelManga:
    backend = LelManga()
    backend._session = FakeSession(page)
    return backend


@respx.mock
async def test_download_chapter_handles_cdn_query_strings(tmp_path: Path) -> None:
    """Page URLs carry a cache-busting query string after the extension."""
    imgs = "".join(
        f'<p><img loading="lazy" src="{_CDN}/{i:03d}.webp?lmv=1784138060"></p>'
        for i in range(1, 4)
    )
    # The site only emits the images inside <noscript>.
    respx.get(url__startswith=_CDN).mock(return_value=httpx.Response(200, content=b"img"))

    await _backend(_reader_page(f"<noscript>{imgs}</noscript>")).download_chapter("/c-1", tmp_path)

    assert sorted(p.name for p in tmp_path.iterdir()) == ["001.webp", "002.webp", "003.webp"]


@respx.mock
async def test_download_chapter_keeps_source_order(tmp_path: Path) -> None:
    """Output filenames follow document order, not the source filenames."""
    imgs = "".join(
        f'<p><img src="{_CDN}/{name}"></p>' for name in ("page_b.jpg", "page_a.PNG", "z.jpeg")
    )
    respx.get(url__startswith=_CDN).mock(return_value=httpx.Response(200, content=b"img"))

    await _backend(_reader_page(imgs)).download_chapter("/c-1", tmp_path)

    assert sorted(p.name for p in tmp_path.iterdir()) == ["001.jpg", "002.png", "003.jpeg"]


async def test_download_chapter_rejects_non_page_images(tmp_path: Path) -> None:
    """Banners and unsupported types must not be mistaken for chapter pages."""
    body = (
        '<img src="https://www.lelmanga.com/wp-content/themes/logo.png">'
        f'<img src="{_CDN}/ad.gif?lmv=1">'
    )

    with pytest.raises(RuntimeError, match="No content images found"):
        await _backend(_reader_page(body)).download_chapter("/c-1", tmp_path)

    assert not list(tmp_path.iterdir())


async def test_download_chapter_requires_reader_area(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="No #readerarea found"):
        await _backend("<html><body>nope</body></html>").download_chapter("/c-1", tmp_path)
