"""Shared pytest fixtures."""

from __future__ import annotations

import pytest

from mangadown.config import Settings


@pytest.fixture
def tmp_settings(tmp_path: object) -> Settings:
    """Settings with all paths pointing at a temp directory."""
    from pathlib import Path

    p = Path(str(tmp_path))
    return Settings(
        mal_user="testuser",
        gmail_user="test@gmail.com",
        gmail_password="secret",
        kindle_email="test@kindle.com",
        cache_dir=p / "cache",
        output_dir=p / "output",
        tracked_file=p / "tracked",
    )
