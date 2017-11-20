#! /usr/bin/env python3

from api import mal, kindle, gmail
from api.backends import backends
from api.settings import *
import argparse
import sys
import os
import shutil
import asyncio
from collections import defaultdict


parser = argparse.ArgumentParser(description="Manga downloader")
parser.add_argument('-l', "--list-mangas", action="store_true",
                    dest="list_mangas", help="List available mangas")
parser.add_argument('-m', "--list-mal", dest="list_mal", action="store_true",
                    help="List MyAnimeList mangas for user")
parser.add_argument('-a', "--mangas", type=str, nargs='+', default=[],
                    help="Mangas to download, added to the tracked file")
args = parser.parse_args()

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

tracked = args.mangas
with open("tracked") as f:
    for line in f.read().split('\n'):
        line = line.strip()
        if line != '' and not line.startswith('#'):
            tracked.append(line)

for manga in tracked:
    print("# Updating " + manga, end='', flush=True)
    chapters = defaultdict(list)
    for b in backends:
        if manga in mangas[b.__name__]:
            code = mangas[b.__name__][manga]
            for chap, url in b.get_chapters(code).items():
                chapters[chap].append((b, url))
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
            print("{}, ".format(chap_str), end='', flush=True)
            success = False
            for backend, url in chapters[chap]:
                try:
                    backend.download_chapter(url, path, loop)
                    kindle.dir_to_mobi(path)
                    shutil.rmtree(path)
                    success = True
                    break
                except KeyboardInterrupt:
                    raise
                except:
                    print("({} X), ".format(backend.__name__), end='', flush=True)
                    try:
                        os.remove(path + ".mobi")
                        shutil.rmtree(path)
                    except:
                        pass
            if not success:
                print("FAIL")
            else:
                gmail.send_mail(KINDLE_MAIL, folder, [path + ".mobi"])
    print("done.")
