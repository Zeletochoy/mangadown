#! /usr/bin/env python3

from pathlib import Path
from typing import List

import click

from .. import OUTPUT_DIR
from ..api import gmail, settings


@click.command()
@click.argument("filepaths", type=click.Path(exists=True), nargs=-1)
def main(filepaths: List[click.Path]) -> None:
    if filepaths:
        filepaths = [Path(p) for p in filepaths]
    else:
        filepaths = list(OUTPUT_DIR.iterdir())

    for path in filepaths:
        print(f"Sending {path.stem}...")
        gmail.send_mail(settings.KINDLE_MAIL, path.stem, [path])
