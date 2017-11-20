from . import mal
from .backends import Backends
from .settings import *
import os
import asyncio
from collections import defaultdict
from functools import lru_cache


loop = asyncio.get_event_loop()
os.makedirs("output", exist_ok=True)


@lru_cache(1)
def get_mangas():
    return list(sorted(Backends.get_mangas()))


@lru_cache(1)
def get_progress():
    return mal.get_manga_progress(MAL_USER)


def update_manga(manga):
    print("# Updating " + manga, end='', flush=True)
    chapters = Backends.get_chapters(manga)
    if len(chapters) == 0:
        print(": no available chapters.")
        return
    progress = get_progress()
    current = progress[mal.get_mal_title(manga)]
    last = str(max(chapters)).rstrip('0').rstrip('.')
    print(" ({}/{})".format(current, last))
    for chap in (c for c in sorted(chapters) if c > current):
        chap_str = str(chap).rstrip('0').rstrip('.')
        folder = "{} {}".format(manga, chap_str)
        path = os.path.join("output", folder)
        mobi = path + ".mobi"
        if os.path.isfile(mobi):
            continue
        print("{}".format(chap_str), end='')
        success = Backends.download_chapter(manga, chap, path, loop)
        if not success:
            print(" FAIL", end='')
        print(", ", end='', flush=True)
    print("done.")
