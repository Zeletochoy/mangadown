"""Backend protocol and registry."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from mangadown.cache import Cache


@runtime_checkable
class Backend(Protocol):
    """Interface that all manga source backends must implement."""

    @property
    def name(self) -> str: ...

    def get_mangas(self, cache: Cache) -> dict[str, str]:
        """Return ``{title: url}`` for all available manga."""
        ...

    def get_chapters(self, manga_url: str) -> dict[float, str]:
        """Return ``{chapter_number: chapter_url}`` for a manga."""
        ...

    async def download_chapter(self, chapter_url: str, dest: Path) -> None:
        """Download chapter images into *dest*."""
        ...


def get_backends() -> list[Backend]:
    """Return all registered backend instances."""
    from mangadown.backends.lelmanga import LelManga

    return [LelManga()]
