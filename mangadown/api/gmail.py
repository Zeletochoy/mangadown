from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
import smtplib
import threading

from . import settings


def send_mail(to, subject, files=[]):
    msg = MIMEMultipart()
    msg["From"] = settings.GMAIL_USER
    msg["To"] = to
    msg["Subject"] = subject

    for path in files:
        part = MIMEBase("application", "octet-stream")
        with open(path, "rb") as f:
            part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f"attachment; filename=\"{path.name}\"")
        msg.attach(part)

    server = smtplib.SMTP('smtp.gmail.com:587')
    server.ehlo_or_helo_if_needed()
    server.starttls()
    server.ehlo_or_helo_if_needed()
    server.login(settings.GMAIL_USER, settings.GMAIL_PASS)
    server.sendmail(settings.GMAIL_USER, to, msg.as_string())
    server.quit()


# Same parameters as send_mail
def send_mail_async(*args, **kwargs):
    thread = threading.Thread(target=send_mail, args=args, kwargs=kwargs)
    thread.start()
