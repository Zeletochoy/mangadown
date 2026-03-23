"""Tests for cli/main.py."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from mangadown.cli.main import cli
from mangadown.config import Settings


def _make_settings(tmp_path: Path) -> Settings:
    return Settings(
        mal_user="",
        gmail_user="",
        gmail_password="",
        kindle_email="",
        cache_dir=tmp_path / "cache",
        output_dir=tmp_path / "output",
        tracked_file=tmp_path / "tracked",
    )


def test_help() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "mangadown" in result.output


def test_download_help() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["download", "--help"])
    assert result.exit_code == 0
    assert "--list" in result.output
    assert "--no-cache" in result.output


def test_send_help() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["send", "--help"])
    assert result.exit_code == 0


def test_download_list(tmp_path: Path) -> None:
    class FakeBackend:
        name = "fake"

        def get_mangas(self, cache):
            return {"alpha": "/a", "beta": "/b"}

    settings = _make_settings(tmp_path)

    with (
        patch("mangadown.config.Settings", return_value=settings),
        patch("mangadown.backends.get_backends", return_value=[FakeBackend()]),
    ):
        runner = CliRunner()
        result = runner.invoke(cli, ["download", "--list"])
        assert result.exit_code == 0
        assert "alpha" in result.output
        assert "beta" in result.output


def test_download_list_empty(tmp_path: Path) -> None:
    class FakeBackend:
        name = "fake"

        def get_mangas(self, cache):
            return {}

    settings = _make_settings(tmp_path)

    with (
        patch("mangadown.config.Settings", return_value=settings),
        patch("mangadown.backends.get_backends", return_value=[FakeBackend()]),
    ):
        runner = CliRunner()
        result = runner.invoke(cli, ["download", "--list"])
        assert result.exit_code == 0
        assert result.output.strip() == ""


def test_download_no_manga_no_tracked(tmp_path: Path) -> None:
    settings = _make_settings(tmp_path)

    with patch("mangadown.cli.main.Settings", return_value=settings):
        runner = CliRunner()
        result = runner.invoke(cli, ["download"])
        assert result.exit_code == 1
        assert "no manga" in result.output.lower()
