from datetime import datetime, timezone

from app.utils.email_client import EmailClient

from app.config import settings

class EmailService:

    @staticmethod
    def send_verify_email(email: str, username: str, url: str):
        subject = "Подтверждение регистрации"
        html = EmailClient.render(
            template_path="template_verify_email.html",
            user_name=username,
            confirmation_url=url,
            expiry_minutes=120,
            site_name="CityVibe",
            site_url=settings.URL,
            support_email="support@example.com",
            year=datetime.now(timezone.utc).year
        )
        body = EmailClient.render(
            template_path="template_verify_email.txt",
            username=username,
            url=url
        )
        EmailClient.send_email(
            to=email,
            subject=subject,
            html=html,
            body=body
        )

if __name__ == "__main__":
    EmailService.send_verify_email("sdfsd@test.ru", "qqqq", "sdfdsfdsfdsfsdf")