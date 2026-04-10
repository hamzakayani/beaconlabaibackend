import smtplib
from app.core.config import settings


class SMTPClient:
    def __init__(self):
        self.server = None

    def connect(self):
        if self.server is None:
            self.server = smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT)
            self.server.ehlo()
            self.server.starttls()
            self.server.ehlo()
            self.server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)

    def send(self, from_email, recipients, message):
        if self.server is None:
            self.connect()

        self.server.sendmail(from_email, recipients, message)

    def close(self):
        if self.server:
            try:
                self.server.quit()
            except Exception:
                pass
            self.server = None