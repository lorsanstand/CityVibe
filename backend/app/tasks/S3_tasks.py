from typing import List
import uuid
import asyncio
import logging

from app.celery_app import celery_app
from app.services.S3_service import EventPhotoService
from app.celery_db import get_celery_async_session_maker, reset_celery_db

log = logging.getLogger(__name__)

class EventPhotoTasks:
    @staticmethod
    @celery_app.task
    def add_new_photos_task(event_uuid: uuid.UUID, photos: List[bytes]):
        log.info("Celery task: Adding photos to S3", extra={"event_id": str(event_uuid), "count": len(photos)})
        try:
            reset_celery_db()
            asyncio.run(EventPhotoService.add_new_photos(event_uuid, photos, get_celery_async_session_maker()))
            log.info("Celery task completed: Photos added to S3", extra={"event_id": str(event_uuid)})
        except Exception as e:
            log.error(f"Celery task failed: {str(e)}", extra={"event_id": str(event_uuid)})
            raise


    @staticmethod
    @celery_app.task
    def delete_photos_task(photo_names: List[str]):
        log.info("Celery task: Deleting photos from S3", extra={"count": len(photo_names)})
        try:
            reset_celery_db()
            asyncio.run(EventPhotoService.delete_photos(photo_names, get_celery_async_session_maker()))
            log.info("Celery task completed: Photos deleted from S3", extra={"count": len(photo_names)})
        except Exception as e:
            log.error(f"Celery task failed: {str(e)}", extra={"count": len(photo_names)})
            raise


