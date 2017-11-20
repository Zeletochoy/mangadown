#! /usr/bin/env python3

from kcc import comic2ebook
import sys
import os


def dir_to_mobi(path, title=None, authors=None):
    argv = "-m -f MOBI -p K45 -c 1".split()
    if title is not None:
        argv += ["-t", title]
    if authors is not None:
        argv += ["-a"] + authors
    argv.append(path)

    stdout = sys.stdout
    with open(os.devnull, 'w') as devnull:
        sys.stdout = devnull
        try:
            comic2ebook.main(argv)
        except:
            sys.stdout = stdout
            raise
    sys.stdout = stdout


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: {} chapter_dir".format(sys.argv[0]))
        sys.exit(1)

    dir_to_mobi(sys.argv[1])
