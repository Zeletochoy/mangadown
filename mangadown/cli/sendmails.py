#! /usr/bin/env python3

from pathlib import Path
from typing import List

import click

from .. import OUTPUT_PATH
from ..api import gmail, settings


@click.command()
@click.argument("filepaths", type=click.Path(exists=True))
def main(filepaths: List[click.Path]) -> None:
    if filepaths:
        filepaths = [Path(p) for p in filepaths]
    else:
        filepaths = list(OUTPUT_PATH.iterdir())

    for path in filepaths:
        print(f"Sending {path.stem}...")
        gmail.send_mail(settings.KINDLE_MAIL, path.stem, [path])
