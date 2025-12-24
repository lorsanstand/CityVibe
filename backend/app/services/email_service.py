from datetime import datetime, timezone
import logging

from app.utils.email_client import EmailClient

from app.config import settings

log = logging.getLogger(__name__)

class EmailService:

    @staticmethod
    def send_verify_email(email: str, username: str, url: str):
        log.info("Sending verification email", extra={"email": email, "username": username})
        try:
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
            log.info("Verification email sent successfully", extra={"email": email})
        except Exception as e:
            log.error(f"Failed to send verification email: {str(e)}", extra={"email": email})
            raise

if __name__ == "__main__":
    EmailService.send_verify_email("sdfsd@test.ru", "qqqq", "sdfdsfdsfdsfsdf")