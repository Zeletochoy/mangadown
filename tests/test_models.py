"""Tests for models.py."""

from __future__ import annotations

import pytest

from mangadown.models import Chapter, MalProgress, Manga


class TestChapterLabel:
    @pytest.mark.parametrize(
        ("number", "expected"),
        [
            (42.0, "42"),
            (42.5, "42.5"),
            (100.0, "100"),
            (1.0, "1"),
            (0.5, "0.5"),
            (1053.5, "1053.5"),
        ],
    )
    def test_label_formatting(self, number: float, expected: str) -> None:
        ch = Chapter(number=number, url="http://example.com", backend="test")
        assert ch.label == expected


def test_manga_is_frozen() -> None:
    m = Manga(title="one piece", url="/manga/one-piece", backend="lelmanga")
    with pytest.raises(AttributeError):
        m.title = "other"  # type: ignore[misc]


def test_mal_progress() -> None:
    p = MalProgress(title="One Piece", chapters_read=1100)
    assert p.title == "One Piece"
    assert p.chapters_read == 1100
