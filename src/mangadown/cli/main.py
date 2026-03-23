"""CLI entry point: ``mangadown download`` and ``mangadown send``."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import click

from mangadown.config import Settings


def _setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(message)s",
        stream=sys.stderr,
    )


def _user_choice(prompt: str, candidates: list[str]) -> str:
    """Interactive prompt for disambiguation."""
    click.echo(prompt)
    for i, c in enumerate(candidates):
        click.echo(f"  [{i}] {c}")
    while True:
        raw = click.prompt("Choice", default="0")
        try:
            idx = int(raw)
            if 0 <= idx < len(candidates):
                return candidates[idx]
        except ValueError:
            pass
        click.echo("Invalid choice, try again")


@click.group()
def cli() -> None:
    """mangadown — automated manga downloader for Kindle."""


@cli.command()
@click.argument("mangas", nargs=-1)
@click.option("-l", "--list", "list_mangas_flag", is_flag=True, help="List available manga.")
@click.option("-m", "--list-mal", is_flag=True, help="List MAL reading progress.")
@click.option("--no-cache", is_flag=True, help="Ignore cached manga lists.")
@click.option("-v", "--verbose", is_flag=True, help="Enable debug logging.")
def download(
    mangas: tuple[str, ...],
    list_mangas_flag: bool,
    list_mal: bool,
    no_cache: bool,
    verbose: bool,
) -> None:
    """Download new manga chapters."""
    _setup_logging(verbose)

    from mangadown.backends import get_backends
    from mangadown.mal import get_reading_list
    from mangadown.orchestrator import list_mangas as _list_mangas
    from mangadown.orchestrator import run_updates
    from mangadown.tracked import load_tracked

    settings = Settings()
    backends = get_backends()

    if list_mangas_flag:
        for title in _list_mangas(backends, settings, use_cache=not no_cache):
            click.echo(title)
        return

    if list_mal:
        if not settings.mal_user:
            click.echo("MANGADOWN_MAL_USER not set", err=True)
            raise SystemExit(1)
        for entry in get_reading_list(settings.mal_user):
            click.echo(f"{entry.title}: {entry.chapters_read}")
        return

    # Determine which manga to update.
    titles = list(mangas) if mangas else load_tracked(settings.tracked_file)
    if not titles:
        msg = "No manga specified. Pass titles as arguments or set up a tracked file."
        click.echo(msg, err=True)
        click.echo(f"Tracked file: {settings.tracked_file}", err=True)
        raise SystemExit(1)

    def chooser(candidates: list[str]) -> str:
        return _user_choice("Choose MAL title:", candidates)

    run_updates(
        titles,
        backends,
        settings,
        use_cache=not no_cache,
        chooser=chooser,
    )


@cli.command()
@click.argument("files", nargs=-1, type=click.Path(exists=True, path_type=Path))
@click.option("-v", "--verbose", is_flag=True, help="Enable debug logging.")
def send(files: tuple[Path, ...], verbose: bool) -> None:
    """Send EPUB files to Kindle via email."""
    _setup_logging(verbose)

    from mangadown.email import send_epub

    settings = Settings()

    if not all([settings.gmail_user, settings.gmail_password, settings.kindle_email]):
        click.echo(
            "Missing email config. Set MANGADOWN_GMAIL_USER, MANGADOWN_GMAIL_PASSWORD, "
            "and MANGADOWN_KINDLE_EMAIL.",
            err=True,
        )
        raise SystemExit(1)

    # Default to all EPUBs in output_dir.
    epub_files = list(files) if files else sorted(settings.output_dir.glob("*.epub"))
    if not epub_files:
        click.echo("No EPUB files to send.")
        return

    for f in epub_files:
        click.echo(f"Sending: {f.name}")
        send_epub(
            to=settings.kindle_email,
            subject=f.stem,
            files=[f],
            gmail_user=settings.gmail_user,
            gmail_password=settings.gmail_password,
        )

    click.echo("Done.")
