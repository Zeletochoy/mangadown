"""Tests for the mangamoins backend's API handling and URL construction."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx
import pytest
import respx

from mangadown.backends.lelmanga import LelManga
from mangadown.backends.mangamoins import MangaMoins
from mangadown.cache import Cache

# A real pagesBaseUrl: "bztmrkeiyoushi" and the "_b" suffix are filler the
# site's reader strips before requesting pages.
_RAW_BASE = "https://scans.example.test/bztmrkeiyoushi471c397f1c5d_b/"
_CLEAN_BASE = "https://scans.example.test/471c397f1c5d/"


@dataclass
class FakeResponse:
    payload: Any = None
    status_code: int = 200

    def json(self) -> Any:
        return self.payload


@dataclass
class FakeSession:
    """Stand-in for the curl_cffi session (the site is the system boundary)."""

    routes: dict[str, Any]
    status: int = 200
    cookies: dict[str, str] = field(default_factory=lambda: {"mm_session": "abc"})
    requested: list[str] = field(default_factory=list)

    def get(self, url: str, params: dict[str, Any] | None = None, **_: Any) -> FakeResponse:
        self.requested.append(url)
        for endpoint, payload in self.routes.items():
            if url.endswith(endpoint):
                if callable(payload):
                    payload = payload(params or {})
                return FakeResponse(payload, self.status)
        return FakeResponse(None, self.status)  # an HTML page load


def _backend(routes: dict[str, Any], status: int = 200) -> MangaMoins:
    return _backend_with_session(routes, status)[0]


def _backend_with_session(
    routes: dict[str, Any], status: int = 200
) -> tuple[MangaMoins, FakeSession]:
    """As `_backend`, but also returns the fake session to inspect requests."""
    backend = MangaMoins()
    session = FakeSession(routes, status)
    backend._session = session
    return backend, session


# ----------------------------------------------------------------------
# download_chapter
# ----------------------------------------------------------------------


@respx.mock
async def test_download_chapter_strips_url_filler(tmp_path: Path) -> None:
    """The padded base URL must be cleaned before requesting pages."""
    backend = _backend({"/api/v1/scan": {"pagesBaseUrl": _RAW_BASE, "pageNumbers": 3}})
    route = respx.get(url__startswith=_CLEAN_BASE).mock(
        return_value=httpx.Response(200, content=b"img")
    )

    await backend.download_chapter("/scan/OP1181", tmp_path)

    assert sorted(p.name for p in tmp_path.iterdir()) == ["001.webp", "002.webp", "003.webp"]
    # Source pages are two-digit, and no filler may survive into the request.
    assert sorted(str(c.request.url) for c in route.calls) == [
        f"{_CLEAN_BASE}01.webp",
        f"{_CLEAN_BASE}02.webp",
        f"{_CLEAN_BASE}03.webp",
    ]


@respx.mock
async def test_download_chapter_pads_destination_names(tmp_path: Path) -> None:
    """Destination names stay zero-padded so reading order survives sorting."""
    backend = _backend({"/api/v1/scan": {"pagesBaseUrl": _RAW_BASE, "pageNumbers": 12}})
    respx.get(url__startswith=_CLEAN_BASE).mock(return_value=httpx.Response(200, content=b"i"))

    await backend.download_chapter("/scan/OP1181", tmp_path)

    names = sorted(p.name for p in tmp_path.iterdir())
    assert names[0] == "001.webp"
    assert names[-1] == "012.webp"
    assert len(names) == 12


@pytest.mark.parametrize(
    "payload",
    [
        {"pagesBaseUrl": _RAW_BASE, "pageNumbers": 0},
        {"pagesBaseUrl": _RAW_BASE},
        {"pageNumbers": 5},
        {"pagesBaseUrl": _RAW_BASE, "pageNumbers": "lots"},
    ],
)
async def test_download_chapter_rejects_unusable_payload(payload: dict, tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="No pages listed"):
        await _backend({"/api/v1/scan": payload}).download_chapter("/scan/OP1181", tmp_path)


async def test_download_chapter_reports_api_error(tmp_path: Path) -> None:
    backend = _backend({"/api/v1/scan": {"error": "Unauthorized"}})
    with pytest.raises(RuntimeError, match="Unauthorized"):
        await backend.download_chapter("/scan/OP1181", tmp_path)


async def test_download_chapter_reports_http_error(tmp_path: Path) -> None:
    backend = _backend({"/api/v1/scan": {"pageNumbers": 3}}, status=403)
    with pytest.raises(RuntimeError, match="returned 403"):
        await backend.download_chapter("/scan/OP1181", tmp_path)


async def test_download_chapter_rejects_bad_url(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="Not a mangamoins scan url"):
        await _backend({}).download_chapter("/manga/one_piece", tmp_path)


async def test_download_chapter_loads_page_before_api(tmp_path: Path) -> None:
    """The API only answers a session that has loaded the chapter's page."""
    backend, session = _backend_with_session(
        {"/api/v1/scan": {"pagesBaseUrl": _RAW_BASE, "pageNumbers": 1}}
    )
    with respx.mock:
        respx.get(url__startswith=_CLEAN_BASE).mock(return_value=httpx.Response(200, content=b"i"))
        await backend.download_chapter("/scan/OP1181", tmp_path)

    assert session.requested[0].endswith("/scan/OP1181")
    assert "/api/v1/scan" in session.requested[1]


# ----------------------------------------------------------------------
# get_chapters
# ----------------------------------------------------------------------


def test_get_chapters_maps_numbers_to_scan_urls() -> None:
    backend = _backend(
        {
            "/api/v1/manga": {
                "info": {"title": "One Piece"},
                "chapters": [
                    {"slug": "OP1192", "num": 1192, "title": "x"},
                    {"slug": "OP1181", "num": 1181, "title": "y"},
                    {"slug": "OP10_5", "num": 10.5, "title": "half"},
                ],
            }
        }
    )
    assert backend.get_chapters("/manga/one_piece") == {
        1192.0: "/scan/OP1192",
        1181.0: "/scan/OP1181",
        10.5: "/scan/OP10_5",
    }


def test_get_chapters_skips_malformed_entries() -> None:
    backend = _backend(
        {
            "/api/v1/manga": {
                "chapters": [
                    {"slug": "OP1", "num": 1},
                    {"slug": "OP2"},
                    {"num": 3},
                    {"slug": "OP4", "num": "not-a-number"},
                ]
            }
        }
    )
    assert backend.get_chapters("/manga/one_piece") == {1.0: "/scan/OP1"}


def test_get_chapters_handles_empty_list() -> None:
    assert _backend({"/api/v1/manga": {"info": {}}}).get_chapters("/manga/one_piece") == {}


# ----------------------------------------------------------------------
# get_mangas
# ----------------------------------------------------------------------


def _paged(pages: dict[int, list[dict]], total: int, limit: int = 10):
    def route(params: dict[str, Any]) -> dict[str, Any]:
        page = int(params.get("page", 1))
        return {"total": total, "page": page, "limit": limit, "data": pages.get(page, [])}

    return route


def test_get_mangas_paginates_and_normalises_titles(tmp_path: Path) -> None:
    routes = {
        "/api/v1/mangas": _paged(
            {
                1: [{"mangaSlug": "one_piece"}, {"mangaSlug": "punk_gun"}],
                2: [{"mangaSlug": "someone_hertz"}],
            },
            total=3,
            limit=2,
        )
    }
    mangas = _backend(routes).get_mangas(Cache(tmp_path, "mangamoins"))

    assert mangas == {
        "one piece": "/manga/one_piece",
        "punk gun": "/manga/punk_gun",
        "someone hertz": "/manga/someone_hertz",
    }


def test_get_mangas_stops_on_empty_page(tmp_path: Path) -> None:
    """A wrong `total` must not loop forever."""
    routes = {"/api/v1/mangas": _paged({1: [{"mangaSlug": "one_piece"}]}, total=999)}
    mangas = _backend(routes).get_mangas(Cache(tmp_path, "mangamoins"))
    assert mangas == {"one piece": "/manga/one_piece"}


def test_get_mangas_uses_cache(tmp_path: Path) -> None:
    cache = Cache(tmp_path, "mangamoins")
    cache.set("mangas", {"cached": "/manga/cached"})
    backend, session = _backend_with_session(
        {"/api/v1/mangas": _paged({1: [{"mangaSlug": "fresh"}]}, total=1)}
    )

    assert backend.get_mangas(cache) == {"cached": "/manga/cached"}
    assert session.requested == []


def test_title_keys_match_lelmanga() -> None:
    """Fallback only works if both backends key the same manga identically.

    lelmanga derives titles from a hyphenated slug, mangamoins from an
    underscored one; both must land on the same index key.
    """
    assert MangaMoins._title("one_piece") == "one piece"
    # lelmanga's normalisation, from its get_mangas
    assert "one-piece".replace("-", " ").lower() == MangaMoins._title("one_piece")
    assert isinstance(LelManga().name, str)


def test_get_mangas_terminates_on_duplicate_heavy_catalogue(tmp_path: Path) -> None:
    """The catalogue lists one row per recent chapter, so series repeat.

    Distinct titles therefore never reach `total`; termination must count rows
    or the backend walks every page.
    """
    page1 = [{"mangaSlug": s} for s in ("one_piece", "gachiakuta", "black_clover")]
    dupes = [{"mangaSlug": "spy_x_family"}] * 3
    routes = {"/api/v1/mangas": _paged({1: page1, 2: dupes, 3: dupes}, total=9, limit=3)}
    backend, session = _backend_with_session(routes)

    mangas = backend.get_mangas(Cache(tmp_path, "mangamoins"))

    assert mangas == {
        "one piece": "/manga/one_piece",
        "gachiakuta": "/manga/gachiakuta",
        "black clover": "/manga/black_clover",
        "spy x family": "/manga/spy_x_family",
    }
    # 9 rows at 3 per page: three catalogue pages, each preceded by a page load.
    api_calls = [u for u in session.requested if "/api/v1/mangas" in u]
    assert len(api_calls) == 3


def test_get_mangas_stops_on_short_page(tmp_path: Path) -> None:
    """A page shorter than `limit` is the last one, even if `total` disagrees."""
    routes = {
        "/api/v1/mangas": _paged(
            {1: [{"mangaSlug": "a"}, {"mangaSlug": "b"}], 2: [{"mangaSlug": "c"}]},
            total=999,
            limit=2,
        )
    }
    backend, session = _backend_with_session(routes)
    mangas = backend.get_mangas(Cache(tmp_path, "mangamoins"))

    assert set(mangas) == {"a", "b", "c"}
    assert len([u for u in session.requested if "/api/v1/mangas" in u]) == 2


def test_get_mangas_primes_an_existing_page(tmp_path: Path) -> None:
    """/explorer is a 404 and grants nothing; the catalogue lives on the homepage."""
    backend, session = _backend_with_session(
        {"/api/v1/mangas": _paged({1: [{"mangaSlug": "a"}]}, total=1, limit=10)}
    )
    backend.get_mangas(Cache(tmp_path, "mangamoins"))

    primed = [u for u in session.requested if "/api/v1" not in u]
    assert primed and all(u.rstrip("/").endswith("mangamoins.com") for u in primed)
