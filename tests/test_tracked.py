"""Tests for tracked.py."""

from __future__ import annotations

from pathlib import Path

from mangadown.tracked import load_tracked


def test_basic(tmp_path: Path) -> None:
    f = tmp_path / "tracked"
    f.write_text("one piece\ndragon ball super\n")
    assert load_tracked(f) == ["one piece", "dragon ball super"]


def test_comments_and_blanks(tmp_path: Path) -> None:
    f = tmp_path / "tracked"
    f.write_text("# my manga list\n\none piece\n  # disabled\n  dragon ball super  \n\n")
    assert load_tracked(f) == ["one piece", "dragon ball super"]


def test_case_normalization(tmp_path: Path) -> None:
    f = tmp_path / "tracked"
    f.write_text("One Piece\nDRAGON BALL SUPER\n")
    assert load_tracked(f) == ["one piece", "dragon ball super"]


def test_missing_file(tmp_path: Path) -> None:
    assert load_tracked(tmp_path / "nonexistent") == []


def test_empty_file(tmp_path: Path) -> None:
    f = tmp_path / "tracked"
    f.write_text("")
    assert load_tracked(f) == []
