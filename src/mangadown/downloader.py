"""Async image downloader with retry and concurrency control."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

log = logging.getLogger(__name__)

_MAX_CONCURRENT = 8
_TIMEOUT = httpx.Timeout(30.0, connect=10.0)


@retry(
    retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.TransportError)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    reraise=True,
)
async def _download_one(
    client: httpx.AsyncClient,
    url: str,
    dest: Path,
    semaphore: asyncio.Semaphore,
) -> None:
    async with semaphore:
        resp = await client.get(url)
        resp.raise_for_status()
        dest.write_bytes(resp.content)


async def download_images(
    urls: dict[str, str],
    dest_dir: Path,
    *,
    headers: dict[str, str] | None = None,
    cookies: dict[str, str] | None = None,
) -> None:
    """Download images concurrently into *dest_dir*.

    *urls* maps ``{filename: image_url}``.  Files are written to
    ``dest_dir / filename``.
    """
    dest_dir.mkdir(parents=True, exist_ok=True)
    semaphore = asyncio.Semaphore(_MAX_CONCURRENT)

    async with httpx.AsyncClient(
        headers=headers or {},
        cookies=cookies or {},
        timeout=_TIMEOUT,
        follow_redirects=True,
    ) as client:
        tasks = [
            _download_one(client, url, dest_dir / fname, semaphore) for fname, url in urls.items()
        ]
        await asyncio.gather(*tasks)
