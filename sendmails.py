#! /usr/bin/env python3

from api import gmail
from api import settings
import os

for fname in os.listdir("output"):
    print("Sending {}...".format(fname))
    gmail.send_mail(settings.KINDLE_MAIL, fname,
                    [os.path.join("output", fname)])
