"""EPUB conversion via KindleComicConverter."""

from __future__ import annotations

import contextlib
import io
import logging
from pathlib import Path

from PIL import ImageFile

log = logging.getLogger(__name__)


def dir_to_epub(image_dir: Path, output_dir: Path, title: str | None = None) -> Path:
    """Convert a directory of manga page images to an EPUB file.

    Returns the path to the generated EPUB.
    """
    from kindlecomicconverter import comic2ebook

    # KCC chokes on truncated images (common with web downloads).
    ImageFile.LOAD_TRUNCATED_IMAGES = True

    argv = [str(image_dir), "-p", "KV", "-m", "-f", "EPUB", "-u", "-o", str(output_dir)]
    if title is not None:
        argv += ["-t", title]

    log.debug("Running KCC: %s", argv)
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        comic2ebook.main(argv)

    # KCC names the output after the input directory.
    epub_path = output_dir / f"{image_dir.name}.epub"
    if not epub_path.exists():
        raise RuntimeError(f"KCC did not produce expected output: {epub_path}")
    return epub_path
