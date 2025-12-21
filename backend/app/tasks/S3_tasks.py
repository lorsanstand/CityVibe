from typing import List
import uuid
import asyncio

from app.celery_app import celery_app
from app.services.S3_service import EventPhotoService
from app.celery_db import get_celery_async_session_maker, reset_celery_db

class EventPhotoTasks:
    @staticmethod
    @celery_app.task
    def add_new_photos_task(event_uuid: uuid.UUID, photos: List[bytes]):
        reset_celery_db()
        asyncio.run(EventPhotoService.add_new_photos(event_uuid, photos, get_celery_async_session_maker()))


    @staticmethod
    @celery_app.task
    def delete_photos_task(photo_names: List[str]):
        reset_celery_db()
        asyncio.run(EventPhotoService.delete_photos(photo_names, get_celery_async_session_maker()))


