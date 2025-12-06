from app.celery_app import celery_app
from app.services.email_service import EmailService


@celery_app.task
def send_verify_email_task(email: str, username: str, url: str):
    EmailService.send_verify_email(email, username, url)