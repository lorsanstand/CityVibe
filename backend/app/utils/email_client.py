import smtplib
import os

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from jinja2 import Environment, FileSystemLoader

from app.config import settings

class EmailClient:
    env = Environment(
        loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), "..", "templates"))
    )

    @classmethod
    def render(cls, template_path: str, **context) -> str:
        template = cls.env.get_template(template_path)
        return template.render(**context)

    @classmethod
    def send_email(cls, to: str, subject: str, html: str, body: str):
        msg = MIMEMultipart()
        msg["Subject"] = subject
        msg["From"] = settings.SMTP_EMAIL
        msg["To"] = to

        msg.attach(MIMEText(html, "html", "utf-8"))
        msg.attach(MIMEText(body, "plain", "utf-8"))

        with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as smtp:
            if not settings.MODE == "DEV":
                smtp.starttls()
                smtp.login(settings.SMTP_EMAIL, settings.SMTP_PASSWORD)
            smtp.send_message(msg)