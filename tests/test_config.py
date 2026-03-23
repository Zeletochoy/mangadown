"""Tests for config.py."""

from __future__ import annotations

from pathlib import Path

import pytest

from mangadown.config import Settings


def test_settings_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MANGADOWN_MAL_USER", "alice")
    monkeypatch.setenv("MANGADOWN_GMAIL_USER", "alice@gmail.com")
    monkeypatch.setenv("MANGADOWN_GMAIL_PASSWORD", "pw123")
    monkeypatch.setenv("MANGADOWN_KINDLE_EMAIL", "alice@kindle.com")

    s = Settings()
    assert s.mal_user == "alice"
    assert s.gmail_user == "alice@gmail.com"
    assert s.gmail_password == "pw123"
    assert s.kindle_email == "alice@kindle.com"


def test_settings_defaults_are_paths() -> None:
    s = Settings()
    assert isinstance(s.cache_dir, Path)
    assert isinstance(s.output_dir, Path)
    assert isinstance(s.tracked_file, Path)


def test_settings_override_paths(tmp_path: Path) -> None:
    s = Settings(cache_dir=tmp_path / "c", output_dir=tmp_path / "o", tracked_file=tmp_path / "t")
    assert s.cache_dir == tmp_path / "c"
    assert s.output_dir == tmp_path / "o"
    assert s.tracked_file == tmp_path / "t"


def test_ensure_dirs_creates_directories(tmp_path: Path) -> None:
    s = Settings(cache_dir=tmp_path / "c", output_dir=tmp_path / "o", tracked_file=tmp_path / "t")
    s.ensure_dirs()
    assert s.cache_dir.is_dir()
    assert s.output_dir.is_dir()
