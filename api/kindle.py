from .kcc import comic2ebook
import sys
import os
from contextlib import contextmanager


def dir_to_mobi(path, title=None, authors=None):
    argv = "-m -f MOBI -p K45 -c 1".split()
    if title is not None:
        argv += ["-t", title]
    if authors is not None:
        argv += ["-a"] + authors
    argv.append(path)

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
