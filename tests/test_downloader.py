"""Tests for the async image downloader's retry behaviour."""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest
import respx

from mangadown.downloader import _is_retryable, download_images

_URL = "https://example.test/img/001.webp"


def _status_error(status: int) -> httpx.HTTPStatusError:
    request = httpx.Request("GET", _URL)
    return httpx.HTTPStatusError(
        "boom", request=request, response=httpx.Response(status, request=request)
    )


@pytest.mark.parametrize("status", [500, 502, 503, 504, 429])
def test_transient_statuses_are_retryable(status: int) -> None:
    assert _is_retryable(_status_error(status))


@pytest.mark.parametrize("status", [400, 401, 403, 404, 410, 451])
def test_client_errors_are_not_retryable(status: int) -> None:
    """A missing or forbidden image will never appear; retrying just wastes requests."""
    assert not _is_retryable(_status_error(status))


def test_transport_errors_are_retryable() -> None:
    assert _is_retryable(httpx.ConnectTimeout("timed out"))


def test_unrelated_exceptions_are_not_retryable() -> None:
    assert not _is_retryable(ValueError("nope"))


@respx.mock
async def test_download_images_retries_server_errors(tmp_path: Path) -> None:
    respx.get(_URL).mock(
        side_effect=[
            httpx.Response(503),
            httpx.Response(200, content=b"payload"),
        ]
    )

    await download_images({"001.webp": _URL}, tmp_path)

    assert (tmp_path / "001.webp").read_bytes() == b"payload"


@respx.mock
async def test_download_images_propagates_404(tmp_path: Path) -> None:
    respx.get(_URL).mock(return_value=httpx.Response(404))

    with pytest.raises(httpx.HTTPStatusError):
        await download_images({"001.webp": _URL}, tmp_path)

    assert not (tmp_path / "001.webp").exists()
