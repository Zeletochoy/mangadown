"""Configuration via environment variables / .env file."""

from __future__ import annotations

from pathlib import Path

from platformdirs import user_cache_dir, user_data_dir
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _default_cache_dir() -> Path:
    return Path(user_cache_dir("mangadown"))


def _default_output_dir() -> Path:
    return Path(user_data_dir("mangadown")) / "output"


def _default_tracked_file() -> Path:
    return Path(user_data_dir("mangadown")) / "tracked"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="MANGADOWN_",
        env_file=".env",
        env_file_encoding="utf-8",
    )

    mal_user: str = ""
    gmail_user: str = ""
    gmail_password: str = ""
    kindle_email: str = ""

    cache_dir: Path = Field(default_factory=_default_cache_dir)
    output_dir: Path = Field(default_factory=_default_output_dir)
    tracked_file: Path = Field(default_factory=_default_tracked_file)

    def ensure_dirs(self) -> None:
        """Create cache and output directories if they don't exist."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
