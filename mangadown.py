#! /usr/bin/env python3

import mangapedia
import mal
import argparse
import sys
import os
import asyncio
from settings import *


parser = argparse.ArgumentParser(description="Manga downloader")
parser.add_argument('-l', "--list-mangas", action="store_true",
                    dest="list_mangas", help="List available mangas")
parser.add_argument('-m', "--list-mal", dest="list_mal", action="store_true",
                    help="List MyAnimeList mangas for user")
args = parser.parse_args()


mangas = mangapedia.get_mangas()

if args.list_mangas:
    for name in sorted(mangas):
        print(name)
    sys.exit(0)

progress = mal.get_manga_progress(MAL_USER)

if args.list_mal:
    for manga, chap in progress.items():
        print("{} ({})".format(manga, chap))
    sys.exit(0)

if not os.path.isfile("tracked"):
    print("Couldn't find 'tracked' file, see README for format")
    sys.exit(1)

loop = asyncio.get_event_loop()
os.makedirs("output", exist_ok=True)

tracked = []
with open("tracked") as f:
    tracked = list(filter(bool, f.read().split('\n')))

for manga in tracked:
    print("# Updating " + manga, end='')
    sys.stdout.flush()
    code = mangas[manga]
    chapters = mangapedia.get_chapters(code)
    current = progress[mal.get_mal_title(manga)]
    last = max(chapters)
    print(" ({}/{})".format(current, last))
    for chap in range(current + 1, last + 1):
        folder = "{} {}".format(manga, chap)
        path = os.path.join("output", folder)
        print("{}, ".format(chap), end='')
        sys.stdout.flush()
        mangapedia.download_chapter(chapters[chap], path, loop)
    print("done.")
