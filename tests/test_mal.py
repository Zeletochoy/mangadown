"""Tests for mal.py."""

from __future__ import annotations

from pathlib import Path

import httpx
import respx

from mangadown.cache import Cache
from mangadown.mal import get_reading_list, resolve_mal_title, search_mal_title


class TestGetReadingList:
    @respx.mock
    def test_single_page(self) -> None:
        respx.get("https://myanimelist.net/mangalist/alice/load.json").mock(
            return_value=httpx.Response(
                200,
                json=[
                    {"manga_title": "One Piece", "num_read_chapters": 1100},
                    {"manga_title": "Naruto", "num_read_chapters": 700},
                ],
            )
        )
        entries = get_reading_list("alice")
        assert len(entries) == 2
        assert entries[0].title == "One Piece"
        assert entries[0].chapters_read == 1100

    @respx.mock
    def test_pagination(self) -> None:
        page1 = [{"manga_title": f"Manga {i}", "num_read_chapters": i} for i in range(300)]
        page2 = [{"manga_title": "Last One", "num_read_chapters": 42}]

        route = respx.get("https://myanimelist.net/mangalist/bob/load.json")
        route.side_effect = [
            httpx.Response(200, json=page1),
            httpx.Response(200, json=page2),
        ]

        entries = get_reading_list("bob")
        assert len(entries) == 301
        assert entries[-1].title == "Last One"

    @respx.mock
    def test_empty_list(self) -> None:
        respx.get("https://myanimelist.net/mangalist/nobody/load.json").mock(
            return_value=httpx.Response(200, json=[])
        )
        assert get_reading_list("nobody") == []


class TestSearchMalTitle:
    @respx.mock
    def test_returns_titles(self) -> None:
        respx.get("https://api.jikan.moe/v4/manga").mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": [
                        {"title": "One Piece"},
                        {"title": "One Piece Party"},
                    ]
                },
            )
        )
        result = search_mal_title("one piece")
        assert result == ["One Piece", "One Piece Party"]

    @respx.mock
    def test_empty_results(self) -> None:
        respx.get("https://api.jikan.moe/v4/manga").mock(
            return_value=httpx.Response(200, json={"data": []})
        )
        assert search_mal_title("nonexistent") == []


class TestResolveMalTitle:
    @respx.mock
    def test_exact_match(self, tmp_path: Path) -> None:
        cache = Cache(tmp_path, "mal")
        respx.get("https://api.jikan.moe/v4/manga").mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": [
                        {"title": "One Piece"},
                        {"title": "One Piece Party"},
                    ]
                },
            )
        )
        result = resolve_mal_title("one piece", cache)
        assert result == "One Piece"
        # Second call should hit cache.
        assert cache.get("one piece") == "One Piece"

    @respx.mock
    def test_uses_cache(self, tmp_path: Path) -> None:
        cache = Cache(tmp_path, "mal")
        cache.set("cached manga", "Cached Manga Title")
        # No HTTP mock needed — should not make any request.
        result = resolve_mal_title("cached manga", cache)
        assert result == "Cached Manga Title"

    @respx.mock
    def test_chooser_called_on_ambiguity(self, tmp_path: Path) -> None:
        cache = Cache(tmp_path, "mal")
        respx.get("https://api.jikan.moe/v4/manga").mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": [
                        {"title": "D.Gray-man"},
                        {"title": "D.Gray-man Reverse"},
                    ]
                },
            )
        )
        chosen = resolve_mal_title(
            "d gray man",
            cache,
            chooser=lambda candidates: candidates[0],
        )
        assert chosen == "D.Gray-man"

    @respx.mock
    def test_no_results(self, tmp_path: Path) -> None:
        cache = Cache(tmp_path, "mal")
        respx.get("https://api.jikan.moe/v4/manga").mock(
            return_value=httpx.Response(200, json={"data": []})
        )
        result = resolve_mal_title("nonexistent manga", cache)
        assert result is None
