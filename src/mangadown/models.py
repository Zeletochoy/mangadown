"""Core data models."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Manga:
    """A manga series available on a backend."""

    title: str
    url: str
    backend: str


@dataclass(frozen=True)
class Chapter:
    """A single chapter of a manga."""

    number: float
    url: str
    backend: str

    @property
    def label(self) -> str:
        """Human-readable chapter number (e.g. 42, not 42.0)."""
        return f"{self.number:g}"


@dataclass(frozen=True)
class MalProgress:
    """Reading progress for a manga on MyAnimeList."""

    title: str
    chapters_read: int
