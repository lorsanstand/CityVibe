from typing import List, Optional, Any
import uuid, time
import re

from fastapi import HTTPException, status

from app.events.dao import EventDao, EventReviewsDao
from app.events.models import EventModel, EventReviewsModel
from app.events.schemas import EventCreate, Event, EventCreateDB, EventUpdate, EventUpdateDB, EventSearch
from app.events.schemas import EventReviews, EventReviewsUpdateDB, EventReviewsCreateDB, EventReviewsCreate, EventReviewsUpdate
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
    async def upload_photo(cls, event_uuid: uuid.UUID, photos: List[bytes], user_id: uuid.UUID) -> List[str]:
        photo_path = []

        async with async_session_maker() as session:
            db_event = await EventDao.find_one_or_none(
                session,
                id=event_uuid
            )

            if not db_event:
                raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Event not found")

            if db_event.user_id != user_id:
                raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Insufficient rights to modify the event")

            for photo in photos:
                url = await s3_client.upload_file(
                    file=photo,
                    object_name=f"{db_event.address.replace(" ", "_")}_{int(time.time())}_{uuid.uuid4().hex}.png",
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


    @classmethod
    async def get_event(cls, event_uuid: uuid.UUID) -> Event:
        async with async_session_maker() as session:
            db_event = await EventDao.find_one_or_none(session, id=event_uuid)

            if db_event is None:
                raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Event not found")

            return db_event

    @classmethod
    async def get_events(cls, event: EventSearch, offset: int, limit: int) -> List[Event]:
        async with async_session_maker() as session:
            filters = [EventModel.is_active == True]

            if event.name:
                filters.append(EventModel.name.ilike(f"%{event.name}%"))
            if event.capacity is not None:
                filters.append(EventModel.capacity >= event.capacity)
            if event.environment is not None:
                filters.append(EventModel.environment == event.environment)
            if event.start is not None:
                filters.append(EventModel.start >= event.start)
            if event.age_rating is not None:
                filters.append(EventModel.age_rating >= event.age_rating)
            if event.average_rating is not None:
                filters.append(EventModel.average_rating >= event.average_rating)

            db_events = await EventDao.find_all(
                session,
                offset,
                limit,
                *filters
            )

            return db_events


    @classmethod
    async def update_event(cls, event_uuid: uuid.UUID, new_event: EventUpdate, user_id: uuid.UUID) -> Event:
        async with async_session_maker() as session:
            db_event = await EventDao.find_one_or_none(session, id=event_uuid)

            if db_event is None:
                raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Event not found")

            if db_event.user_id != user_id:
                raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Insufficient rights to modify the event")

            old_photo_path = db_event.photo_path

            update_event = await EventDao.update(
                session,
                EventModel.id == event_uuid,
                obj_in=EventUpdateDB(
                    **new_event.model_dump()
                )
            )

            delete_photo = list(set(old_photo_path) - set(new_event.photo_path))

            for photo in delete_photo:
                protocol, url, bucket, name = re.split(f"://|/", photo)
                await s3_client.delete_file(name)

            await session.commit()
            return update_event


    @classmethod
    async def delete_event(cls, event_uuid: uuid.UUID, user_id: uuid.UUID) -> None:
        async with async_session_maker() as session:
            db_event = await EventDao.find_one_or_none(session, id=event_uuid, user_id=user_id)

            if db_event is None:
                raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Event not found")

            for photo in db_event.photo_path:
                protocol, url, bucket, name = re.split(f"://|/", photo)
                await s3_client.delete_file(name)

            await EventDao.delete(session, id=db_event.id)
            await session.commit()


class EventReviewsService:
    @classmethod
    async def create_new_review(
            cls,
            user_id: uuid.UUID,
            event_id: uuid.UUID,
            new_review: EventReviewsCreate
    ) -> EventReviews:
        async with async_session_maker() as session:
            exist_review = await EventReviewsDao.find_one_or_none(session, user_id=user_id, event_id=event_id)

            if exist_review:
                raise HTTPException(status.HTTP_409_CONFLICT, detail="Review the already")

            db_review = await EventReviewsDao.add(
                session,
                obj_in=EventReviewsCreateDB(
                    **new_review.model_dump(),
                    user_id=user_id,
                    event_id=event_id
                )
            )
            await session.commit()

            await EventDao.update(
                session,
                EventModel.id == event_id,
                obj_in={"average_rating": await EventReviewsDao.avg_rating(session, event_id=event_id),
                        "count_reviews": await EventReviewsDao.count(session, event_id=event_id)}
            )
            await session.commit()
        return db_review


    @classmethod
    async def get_reviews(
            cls,
            offset: int = 0,
            limit: int = 0,
            user_id: Optional[uuid.UUID] = None,
            event_id: Optional[uuid.UUID] = None
    ) -> List[EventReviews]:
        async with async_session_maker() as session:
            filters = []

            if user_id:
                filters.append(EventReviewsModel.user_id == user_id)
            if event_id:
                filters.append(EventReviewsModel.event_id == event_id)

            db_reviews = await EventReviewsDao.find_all(
                session,
                offset,
                limit,
                *filters
            )
        return db_reviews


    @classmethod
    async def put_review(cls, user_id: uuid.UUID, event_id: uuid.UUID, edit_event: EventReviewsUpdate) -> EventReviews:
        async with async_session_maker() as session:
            db_event = await EventReviewsDao.find_one_or_none(session, user_id=user_id, event_id=event_id)

            if not db_event:
                raise HTTPException(status.HTTP_404_NOT_FOUND, detail="review not found")

            db_edit_event = await EventReviewsDao.update(
                session,
                EventReviewsModel.id == db_event.id,
                obj_in=EventReviewsUpdateDB(
                    **edit_event.model_dump()
                )
            )
            await session.commit()

            await EventDao.update(
                session,
                EventModel.id == event_id,
                obj_in={"average_rating": await EventReviewsDao.avg_rating(session, event_id=event_id)}
            )
            await session.commit()
        return db_edit_event


    @classmethod
    async def delete_review(cls, user_id: uuid.UUID, event_id: uuid.UUID):
        async with async_session_maker() as session:
            db_event = await EventReviewsDao.find_one_or_none(session, user_id=user_id, event_id=event_id)

            if not db_event:
                raise HTTPException(status.HTTP_404_NOT_FOUND, detail="review not found")

            await EventReviewsDao.delete(session, id=db_event.id)
            await session.commit()

            await EventDao.update(
                session,
                EventModel.id == event_id,
                obj_in={"average_rating": await EventReviewsDao.avg_rating(session, event_id=event_id),
                        "count_reviews": await EventReviewsDao.count(session, event_id=event_id)}
            )
            await session.commit()