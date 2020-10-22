import sys
import os
from contextlib import contextmanager

from kindlecomicconverter import comic2ebook



def dir_to_mobi(path, title=None):
    argv = [str(path), "-p", "KV", "-m", "-f", "MOBI", "-u", "-o", str(path.parent)]
    if title is not None:
        argv += ["-t", title]

    with ignore_output():
        comic2ebook.main(argv)


@contextmanager
def ignore_output(ignore_stdout=True, ignore_stderr=False):
    stdout = sys.stdout
    stderr = sys.stderr
    with open(os.devnull, 'w') as devnull:
        if ignore_stdout:
            sys.stdout = devnull
        if ignore_stderr:
            sys.stderr = devnull
        yield
    sys.stdout = stdout
    sys.stderr = stderr
