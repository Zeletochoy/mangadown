import sys
from pathlib import Path

MAL_USER = ""
GMAIL_USER = ""
GMAIL_PASS = ""
KINDLE_MAIL = ""


if any(not x for x in (MAL_USER, GMAIL_USER, GMAIL_PASS, KINDLE_MAIL)):
    here = Path(__file__).resolve()
    print("Missing value in settings, check", here)
    sys.exit(1)
