#! /usr/bin/env python3

import api
import sys
import argparse
import os.path


parser = argparse.ArgumentParser(description="Manga downloader")
parser.add_argument('-l', "--list-mangas", action="store_true",
                    dest="list_mangas", help="List available mangas")
parser.add_argument('-m', "--list-mal", dest="list_mal", action="store_true",
                    help="List MyAnimeList mangas for user")
parser.add_argument('-a', "--mangas", type=str, nargs='+', default=[],
                    help="Mangas to download, added to the tracked file")
args = parser.parse_args()


if args.list_mangas:
    for name in api.get_mangas():
        print(name)
    sys.exit(0)

if args.list_mal:
    for manga, chap in api.get_progress():
        print("{} ({})".format(manga, chap))
    sys.exit(0)

if not os.path.isfile("tracked"):
    print("Couldn't find 'tracked' file, see README for format")
    sys.exit(1)

tracked = args.mangas
with open("tracked") as f:
    for line in f.read().split('\n'):
        line = line.strip()
        if line != '' and not line.startswith('#'):
            tracked.append(line)

for manga in tracked:
    api.update_manga(manga)
