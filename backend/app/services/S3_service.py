from typing import List, Optional
import uuid
from contextlib import asynccontextmanager

from app.database import async_session_maker
from app.events.schemas import EventPhotoCreateDB
from app.events.dao import EventPhotoDao
from app.events.models import EventPhotoModel
from app.utils.S3_client import S3Client
from app.config import settings

# s3_client = S3Client(
#     access_key=settings.S3_ACCESS_KEY_ID,
#     secret_key=settings.S3_SECRET_ACCESS_KEY,
#     endpoint_url=settings.S3_URL,
#     bucket_name=settings.S3_BUCKET_NAME
# )


class EventPhotoService:
    @classmethod
    @asynccontextmanager
    async def _get_s3_client(cls):
        client = S3Client(
            access_key=settings.S3_ACCESS_KEY_ID,
            secret_key=settings.S3_SECRET_ACCESS_KEY,
            endpoint_url=settings.S3_URL,
            bucket_name=settings.S3_BUCKET_NAME
        )
        try:
            yield client
        finally:
            pass



    @classmethod
    async def add_new_photos(cls, event_uuid: uuid.UUID, photos: List[bytes], session_maker=None):
        if session_maker is None:
            session_maker = async_session_maker
            
        async with session_maker() as session:
            async with cls._get_s3_client() as s3_client:
                for photo in photos:

                    photo_name = f"{uuid.uuid4()}.png"

                    url = await s3_client.upload_file(
                        file=photo,
                        object_name=photo_name,
                        content_type="image/png"
                    )

                    await EventPhotoDao.add(
                        session,
                        EventPhotoCreateDB(
                            url=url,
                            event_id=event_uuid,
                            object_name=photo_name
                        )
                    )

                await session.commit()


    @classmethod
    async def delete_photos(cls, photo_names: List[str], session_maker=None):
        if session_maker is None:
            session_maker = async_session_maker

        async with session_maker() as session:
            async with cls._get_s3_client() as s3_client:
                await s3_client.delete_files(object_names=photo_names)

            await EventPhotoDao.delete(session, EventPhotoModel.object_name.in_(photo_names))
            await session.commit()