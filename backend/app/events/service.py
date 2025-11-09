from typing import List
import uuid, time

from fastapi import HTTPException, status, UploadFile

from app.events.dao import EventDao
from app.events.models import EventModel
from app.events.schemas import EventCreate, Event, EventCreateDB
from app.database import async_session_maker
from app.base_utils import s3_client


class EventService:
    @classmethod
    async def create_new_event(cls, user_id: uuid.UUID, new_event: EventCreate) -> Event:
        async with async_session_maker() as session:
            event_exist = await EventDao.find_one_or_none(
                session,
                address=new_event.address
            )

            if event_exist:
                raise HTTPException(status.HTTP_409_CONFLICT, detail="Event the already")

            db_event = await EventDao.add(
                session,
                EventCreateDB(
                    **new_event.model_dump(),
                    user_id=user_id,
                )
            )

            await session.commit()
            return db_event


    @classmethod
    async def upload_photo(cls, event_uuid: uuid.UUID, photos: List[bytes]) -> List[str]:
        photo_path = []

        async with async_session_maker() as session:
            db_event = await EventDao.find_one_or_none(
                session,
                id=event_uuid
            )

            if not db_event:
                raise HTTPException(status.HTTP_409_CONFLICT, detail="Event not found")

            for photo in photos:
                url = await s3_client.upload_file(
                    file=photo,
                    object_name=f"{db_event.address}_{int(time.time())}_{uuid.uuid4().hex}.png",
                    content_type="image/png"
                )
                photo_path.append(url)

            if db_event.photo_path is None:
                db_photo_path = []
            else:
                db_photo_path = db_event.photo_path

            await EventDao.update(
                session,
                EventModel.id == db_event.id,
                obj_in={"photo_path": photo_path + db_photo_path}
            )
            await session.commit()
            return photo_path + db_photo_path