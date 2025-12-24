import logging
from app.celery_app import celery_app
from app.services.email_service import EmailService

log = logging.getLogger(__name__)


@celery_app.task
def send_verify_email_task(email: str, username: str, url: str):
    log.info("Celery task: Sending verification email", extra={"email": email, "username": username})
    try:
        EmailService.send_verify_email(email, username, url)
        log.info("Celery task completed: Verification email sent", extra={"email": email})
    except Exception as e:
        log.error(f"Celery task failed: {str(e)}", extra={"email": email})
        raise