from celery import Celery

from app.config import settings

celery_app = Celery(
    "app.celery_app",
    broker=settings.BROKER_URL,
    backend="rpc://"
)

celery_app.autodiscover_tasks(["app.tasks"])