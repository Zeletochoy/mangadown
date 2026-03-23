"""Simple JSON file cache with per-domain files."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)


class Cache:
    """Key-value cache backed by a JSON file.

    Each domain (e.g. ``lelmanga``, ``mal``) gets its own file in the cache
    directory.
    """

    def __init__(self, cache_dir: Path, name: str) -> None:
        self._path = cache_dir / f"{name}.json"
        self._data: dict[str, Any] | None = None

    def _load(self) -> dict[str, Any]:
        if self._data is not None:
            return self._data
        if self._path.exists():
            try:
                self._data = json.loads(self._path.read_text())
            except (json.JSONDecodeError, OSError) as exc:
                log.warning("Failed to read cache %s: %s", self._path, exc)
                self._data = {}
        else:
            self._data = {}
        return self._data

    def get(self, key: str) -> Any | None:
        """Return cached value for *key*, or ``None`` if absent."""
        return self._load().get(key)

    def set(self, key: str, value: Any) -> None:
        """Store *value* under *key* and flush to disk."""
        data = self._load()
        data[key] = value
        self._flush()

    def get_all(self) -> dict[str, Any]:
        """Return the entire cache dict (or empty dict if no cache)."""
        return dict(self._load())

    def set_all(self, data: dict[str, Any]) -> None:
        """Replace the entire cache and flush to disk."""
        self._data = data
        self._flush()

    def clear(self) -> None:
        """Delete all cached data."""
        self._data = {}
        if self._path.exists():
            self._path.unlink()

    def _flush(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(self._data, ensure_ascii=False))
