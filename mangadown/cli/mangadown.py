#! /usr/bin/env python3

import sys
from typing import List

import click

from .. import api, TRACKED_FILE


@click.command()
@click.argument("mangas", type=str, nargs=-1)
@click.option("-l", "--list-mangas", is_flag=True, help="List available mangas")
@click.option("-m", "--list-mal", is_flag=True, help="List MyAnimeList mangas for user")
def main(mangas: List[str], list_mangas: bool, list_mal: bool) -> None:
    """
    Manga Downloader

    Parameters:
      - mangas: Mangas to download, on top of the tracked file
    """
    if list_mangas:
        for name in api.get_mangas():
            print(name)
        sys.exit(0)

    if list_mal:
        for manga, chap in api.get_progress():
            print("{} ({})".format(manga, chap))
        sys.exit(0)

    if not TRACKED_FILE.is_file():
        print("Couldn't find 'tracked' file, see README for format")
        sys.exit(1)

    tracked = set(mangas)
    with open(TRACKED_FILE) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                tracked.add(line)

    for manga in sorted(tracked):
        api.update_manga(manga)
