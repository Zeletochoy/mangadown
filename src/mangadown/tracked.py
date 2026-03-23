"""Parse the tracked manga file."""

from __future__ import annotations

from pathlib import Path


def load_tracked(path: Path) -> list[str]:
    """Read the tracked file and return manga titles.

    Lines starting with ``#`` are comments.  Blank lines are ignored.
    Titles are stripped and lowered.  Order is preserved.
    """
    if not path.exists():
        return []
    titles: list[str] = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        titles.append(line.lower())
    return titles
