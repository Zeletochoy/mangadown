"""Tests for orchestrator.py."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mangadown.config import Settings
from mangadown.orchestrator import list_mangas, run_updates


class FakeBackend:
    """Minimal backend for testing."""

    def __init__(
        self,
        mangas: dict[str, str] | None = None,
        chapters: dict[float, str] | None = None,
        *,
        fail_download: bool = False,
    ) -> None:
        self._mangas = mangas or {}
        self._chapters = chapters or {}
        self._fail_download = fail_download
        self.downloaded: list[tuple[str, Path]] = []

    @property
    def name(self) -> str:
        return "fake"

    def get_mangas(self, cache):
        return self._mangas

    def get_chapters(self, manga_url: str) -> dict[float, str]:
        return self._chapters

    async def download_chapter(self, chapter_url: str, dest: Path) -> None:
        if self._fail_download:
            raise RuntimeError("Download failed")
        dest.mkdir(parents=True, exist_ok=True)
        # Write a dummy image so the directory isn't empty.
        (dest / "001.png").write_bytes(b"fake image data")
        self.downloaded.append((chapter_url, dest))


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(
        mal_user="",
        gmail_user="",
        gmail_password="",
        kindle_email="",
        cache_dir=tmp_path / "cache",
        output_dir=tmp_path / "output",
        tracked_file=tmp_path / "tracked",
    )


def test_list_mangas(settings: Settings) -> None:
    backend = FakeBackend(mangas={"one piece": "/manga/one-piece", "naruto": "/manga/naruto"})
    result = list_mangas([backend], settings)
    assert result == ["naruto", "one piece"]


def test_list_mangas_empty(settings: Settings) -> None:
    backend = FakeBackend(mangas={})
    result = list_mangas([backend], settings)
    assert result == []


@patch("mangadown.orchestrator.dir_to_epub")
def test_downloads_new_chapters(mock_epub: MagicMock, settings: Settings) -> None:
    backend = FakeBackend(
        mangas={"test manga": "/manga/test"},
        chapters={1.0: "/ch/1", 2.0: "/ch/2"},
    )

    # Make dir_to_epub return a fake epub path.
    def fake_epub(image_dir, output_dir, title=None):
        epub = output_dir / f"{image_dir.name}.epub"
        epub.write_bytes(b"fake epub")
        return epub

    mock_epub.side_effect = fake_epub

    run_updates(["test manga"], [backend], settings)

    assert len(backend.downloaded) == 2
    assert (settings.output_dir / "test manga 1.epub").exists()
    assert (settings.output_dir / "test manga 2.epub").exists()


@patch("mangadown.orchestrator.dir_to_epub")
def test_skips_existing_chapters(mock_epub: MagicMock, settings: Settings) -> None:
    backend = FakeBackend(
        mangas={"test manga": "/manga/test"},
        chapters={1.0: "/ch/1", 2.0: "/ch/2"},
    )

    # Pre-create chapter 1 epub.
    settings.ensure_dirs()
    (settings.output_dir / "test manga 1.epub").write_bytes(b"existing")

    def fake_epub(image_dir, output_dir, title=None):
        epub = output_dir / f"{image_dir.name}.epub"
        epub.write_bytes(b"fake epub")
        return epub

    mock_epub.side_effect = fake_epub

    run_updates(["test manga"], [backend], settings)

    # Only chapter 2 should be downloaded.
    assert len(backend.downloaded) == 1
    assert backend.downloaded[0][0] == "/ch/2"


@patch("mangadown.orchestrator.dir_to_epub")
def test_one_failure_doesnt_abort_others(mock_epub: MagicMock, settings: Settings) -> None:
    """A failed download for chapter 1 should not prevent chapter 2."""
    call_count = 0

    class FailFirstBackend(FakeBackend):
        async def download_chapter(self, chapter_url: str, dest: Path) -> None:
            nonlocal call_count
            call_count += 1
            if chapter_url == "/ch/1":
                raise RuntimeError("Transient failure")
            dest.mkdir(parents=True, exist_ok=True)
            (dest / "001.png").write_bytes(b"data")
            self.downloaded.append((chapter_url, dest))

    backend = FailFirstBackend(
        mangas={"test manga": "/manga/test"},
        chapters={1.0: "/ch/1", 2.0: "/ch/2"},
    )

    def fake_epub(image_dir, output_dir, title=None):
        epub = output_dir / f"{image_dir.name}.epub"
        epub.write_bytes(b"fake epub")
        return epub

    mock_epub.side_effect = fake_epub

    run_updates(["test manga"], [backend], settings)

    # Chapter 1 failed, chapter 2 succeeded.
    assert not (settings.output_dir / "test manga 1.epub").exists()
    assert (settings.output_dir / "test manga 2.epub").exists()


def test_unknown_manga_logged(settings: Settings, caplog: pytest.LogCaptureFixture) -> None:
    backend = FakeBackend(mangas={"one piece": "/manga/one-piece"})
    with caplog.at_level("WARNING"):
        run_updates(["nonexistent"], [backend], settings)
    assert "not found" in caplog.text.lower()
