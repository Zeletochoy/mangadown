from . import lirescan
from . import japscan
from . import scantradfr
from . import scan_fr
from .. import kindle
import logging
import os
import shutil
from collections import defaultdict


# backends = (scantradfr, lirescan, scan_fr)  #japscan)
backends = (scan_fr,)
name2mod = {b.__name__: b for b in backends}


class Backends:
    _mangas = None
    _chapters = defaultdict(lambda: None)

    def get_mangas():
        if Backends._mangas is not None:
            return Backends._mangas
        res = defaultdict(list)
        for backend in backends:
            name = backend.__name__
            mangas = {}
            try:
                mangas = backend.get_mangas()
            except Exception as e:
                logging.warning("{}.get_mangas() failed: {}".format(name, e))
                continue
            for title, url in mangas.items():
                res[title].append((name, url))
        Backends._mangas = res
        return res.keys()


    def get_chapters(title, cached=False):
        if cached  and Backends._chapters[title] is not None:
            return Backends._chapters[title]
        if Backends._mangas is None:
            Backends.get_mangas()
        res = defaultdict(list)
        for back_name, url in Backends._mangas[title]:
            backend = name2mod[back_name]
            chapters = {}
            try:
                chapters = backend.get_chapters(url)
            except Exception as e:
                logging.warning("{}.get_chapters({}) failed: {}".format(back_name, title, e))
                continue
            for num, url in chapters.items():
                res[num].append((back_name, url))
        Backends._chapters[title] = res
        return res.keys()


    def download_chapter(title, num, path, loop):
        if Backends._chapters[title] is None:
            Backends.get_chapters(title)
        chapters = Backends._chapters[title][num]
        if len(chapters) == 0:
            return False
        success = False
        for back_name, url in chapters:
            backend = name2mod[back_name]
            try:
                backend.download_chapter(url, path, loop)
            except Exception as e:
                logging.warning("{}.download_chapter({}, {}) failed: {}".format(back_name, title, num, e))
                if os.path.isdir(path):
                    shutil.rmtree(path)
                continue
            try:
                kindle.dir_to_epub(path)
                shutil.rmtree(path)
                success = True
                break
            except Exception as e:
                logging.warning("dir_to_epub({}) failed: {}".format(path, e))
                if os.path.isdir(path):
                    shutil.rmtree(path)
                epub = path.parent / f"{path.name}.epub"
                if os.path.isfile(epub):
                    os.remove(epub)
        return success
