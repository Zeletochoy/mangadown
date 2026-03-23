"""Tests for cache.py."""

from __future__ import annotations

from pathlib import Path

from mangadown.cache import Cache


def test_get_set_roundtrip(tmp_path: Path) -> None:
    c = Cache(tmp_path, "test")
    assert c.get("key") is None
    c.set("key", {"a": 1})
    assert c.get("key") == {"a": 1}


def test_persistence_across_instances(tmp_path: Path) -> None:
    c1 = Cache(tmp_path, "test")
    c1.set("x", 42)

    c2 = Cache(tmp_path, "test")
    assert c2.get("x") == 42


def test_separate_files_per_name(tmp_path: Path) -> None:
    a = Cache(tmp_path, "alpha")
    b = Cache(tmp_path, "beta")
    a.set("k", "a_val")
    b.set("k", "b_val")
    assert a.get("k") == "a_val"
    assert b.get("k") == "b_val"
    assert (tmp_path / "alpha.json").exists()
    assert (tmp_path / "beta.json").exists()


def test_clear(tmp_path: Path) -> None:
    c = Cache(tmp_path, "test")
    c.set("k", "v")
    assert c.get("k") == "v"
    c.clear()
    assert c.get("k") is None
    assert not (tmp_path / "test.json").exists()


def test_get_all_and_set_all(tmp_path: Path) -> None:
    c = Cache(tmp_path, "test")
    c.set("a", 1)
    c.set("b", 2)
    data = c.get_all()
    assert data == {"a": 1, "b": 2}

    c.set_all({"x": 10})
    assert c.get("x") == 10
    assert c.get("a") is None


def test_missing_cache_dir_is_created(tmp_path: Path) -> None:
    nested = tmp_path / "deep" / "nested"
    c = Cache(nested, "test")
    c.set("k", "v")
    assert (nested / "test.json").exists()


def test_corrupt_json_handled(tmp_path: Path) -> None:
    (tmp_path / "bad.json").write_text("{broken json!!")
    c = Cache(tmp_path, "bad")
    assert c.get("anything") is None
