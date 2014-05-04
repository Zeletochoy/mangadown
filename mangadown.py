#! /usr/bin/env python3

import urllib.request
import os
import shutil
from os.path import expanduser


class Manga:
  def __init__(self, title, dir, max_pages=42):
    self.title = title
    self.dir = dir
    self.max_pages = max_pages

  def update(self):
    first = self.get_last()
    self.get_chapters(range(first, first + 1337))

  def get_chapters(self, numbers):
    for c in numbers:
      dir = os.path.join(
        "D:/", "Mangas/", self.dir, self.dir + " " + str(c))
      try:
        os.makedirs(dir)
      except Exception:
        print("Directory \"{}\" already exists, downloading chapter anyway."
              .format(dir))
      last = 0
      for p in range(self.max_pages):
        f = str(p).zfill(2) + ".jpg"
        url = "http://lelscan.com/mangas/{}/{}/{}".format(self.title, c, f)
        path = os.path.join(dir, f)
        try:
          urllib.request.urlretrieve(url, path)
          last = p
        except Exception as e:
          if last == 0:
            print("{}: stopped at chapter {}".format(self.title, c - 1))
            shutil.rmtree(dir)
            self.save_last(c - 1)
            return
          print("{} {}: stopped at page {}".format(self.title, c, p))
          self.save_last(c)
          try:
            os.remove(path)
          except Exception as ex:
            print("Unexpected exception: {}".format(ex))
          break

  def get_last(self):
    path = os.path.join("D:/", "Mangas/", "last_dl.txt")
    f = open(path, "r")
    lines = f.read().split("\n")
    for l in lines:
      if l == "":
        continue
      fields = l.split(":")
      if fields[0] == self.title:
        return int(fields[1]) + 1
    f.close()
    return 1

  def save_last(self, nb):
    path = os.path.join("D:/", "Mangas/", "last_dl.txt")
    f = open(path, "r")
    lines = f.read().split("\n")
    values = {}
    for l in lines:
      if l == "":
        continue
      fields = l.split(":")
      values[fields[0]] = int(fields[1])
    f.close()
    values[self.title] = nb
    f = open(path, "w")
    for t, n in values.items():
      f.write("{}:{}\n".format(t, n))
    f.close()


def get_mangas():
  mangas = [("one-piece", "One Piece"),
            ("bleach", "Bleach"),
            ("naruto", "Naruto"),
            ("d-gray-man", "D.Gray-Man"),
            ("fairy-tail", "Fairy Tail"),
            ("beelzebub", "Beelzebub"),
            ("toriko", "Toriko")]
  for n, p in mangas:
    yield Manga(n, p)


for m in get_mangas():
  m.update()
