#! /usr/bin/env python3

import mangapedia
import lirescan
import mal
import kindle
import argparse
import sys
import os
import shutil
import asyncio
from settings import *


parser = argparse.ArgumentParser(description="Manga downloader")
parser.add_argument('-l', "--list-mangas", action="store_true",
                    dest="list_mangas", help="List available mangas")
parser.add_argument('-m', "--list-mal", dest="list_mal", action="store_true",
                    help="List MyAnimeList mangas for user")
args = parser.parse_args()

backends = (lirescan ,mangapedia)
mangas = {b.__name__: b.get_mangas() for b in backends}

if args.list_mangas:
    mangas = set(m for backend in mangas.values() for m in backend)
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
    chapters = {}
    for b in backends:
        if manga in mangas[b.__name__]:
            code = mangas[b.__name__][manga]
            for chap, url in b.get_chapters(code).items():
                chapters[chap] = (b, url)
    current = progress[mal.get_mal_title(manga)]
    last = str(max(chapters)).rstrip('0').rstrip('.')
    print(" ({}/{})".format(current, last))
    for chap in sorted(chapters):
        if chap > current:
            chap_str = str(chap).rstrip('0').rstrip('.')
            folder = "{} {}".format(manga, chap_str)
            path = os.path.join("output", folder)
            if os.path.isfile(path + ".mobi"):
                continue
            print("{}, ".format(chap_str), end='')
            sys.stdout.flush()
            backend, url = chapters[chap]
            backend.download_chapter(url, path, loop)
            kindle.dir_to_mobi(path)
            shutil.rmtree(path)
    print("done.")
