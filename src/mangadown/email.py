"""Email delivery via Gmail SMTP."""

from __future__ import annotations

import logging
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from pathlib import Path

log = logging.getLogger(__name__)

_SMTP_HOST = "smtp.gmail.com"
_SMTP_PORT = 587


def send_epub(
    *,
    to: str,
    subject: str,
    files: list[Path],
    gmail_user: str,
    gmail_password: str,
) -> None:
    """Send EPUB files as email attachments via Gmail SMTP."""
    msg = MIMEMultipart()
    msg["Subject"] = subject
    msg["From"] = gmail_user
    msg["To"] = to

    for filepath in files:
        part = MIMEBase("application", "epub+zip")
        part.set_payload(filepath.read_bytes())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f'attachment; filename="{filepath.name}"')
        msg.attach(part)

    log.info("Sending %d file(s) to %s", len(files), to)
    with smtplib.SMTP(_SMTP_HOST, _SMTP_PORT) as server:
        server.starttls()
        server.login(gmail_user, gmail_password)
        server.send_message(msg)
    log.info("Email sent successfully")
