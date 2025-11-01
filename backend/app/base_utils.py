import smtplib
from datetime import datetime, timezone

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from string import Template

from app.config import settings


def render_template_from_file(path: str, **context):
    with open(path, "r", encoding="utf-8") as file:
        tpl = Template(file.read())
    return  tpl.safe_substitute(**context)



def send_verify_email(username: str, email: str, url: str):
    with smtplib.SMTP_SSL(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
        server.login(settings.SMTP_EMAIL, settings.SMTP_PASSWORD)

        msg = MIMEMultipart()
        msg["From"] = settings.SMTP_EMAIL
        msg["To"] = email
        msg["Subject"] = "Подтверждение регистрации"

        # Тело письма — осмысленное и форматированное
        body = f"""
        Здравствуйте, {username}!

        Для подтверждения вашей регистрации перейдите по ссылке:
        {url}

        Если вы не создавали аккаунт — просто проигнорируйте это письмо.

        С уважением,  
        Команда CityVibe
            """

        html = render_template_from_file(
            "app/templates/mail.html",
            user_name=username,
            confirmation_url=url,
            expiry_minutes=120,
            site_name="CityVibe",
            site_url="https://example.com",
            support_email="support@example.com",
            year=datetime.now(timezone.utc).year
        )

        msg.attach(MIMEText(html, "html", "utf-8"))
        msg.attach(MIMEText(body, "plain", "utf-8"))

        server.send_message(msg, settings.SMTP_EMAIL, email)


if __name__ == "__main__":
    send_verify_email("tests", "stasstrochewskij@gmail.com", "dfdfshj")



