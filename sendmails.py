#! /usr/bin/env python3

from api import gmail
from api import settings
import os
import sys

files = sys.argv[1:]
if len(files) == 0:
    files = [os.path.join("output", f) for f in os.listdir("output")]


for fname in files:
    print("Sending {}...".format(fname))
    gmail.send_mail(settings.KINDLE_MAIL, fname, [fname])
