from typing import List, Optional
import uuid
import logging

from fastapi import HTTPException, status

from app.events.dao import EventDao, EventReviewsDao, EventPhotoDao
from app.events.models import EventModel, EventReviewsModel, EventPhotoModel
from app.events.schemas import EventCreate, Event, EventCreateDB, EventUpdate, EventUpdateDB, EventSearch
from app.events.schemas import EventReviews, EventReviewsUpdateDB, EventReviewsCreateDB, EventReviewsCreate, EventReviewsUpdate
from app.events.schemas import EventPhoto
from app.database import async_session_maker
from app.tasks.S3_tasks import EventPhotoTasks

log = logging.getLogger(__name__)


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
            log.info("The event has registered", extra={"user_id": db_event.id})
            return db_event


    @classmethod
    async def upload_photo(cls, event_uuid: uuid.UUID, photos: List[bytes], user_id: uuid.UUID):
        async with async_session_maker() as session:
            db_event = await EventDao.find_one_or_none(
                session,
                id=event_uuid
            )
            if not db_event:
                raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Event not found")

            if db_event.user_id != user_id:
                raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Insufficient rights to modify the event")

            count_photo = await EventPhotoDao.count(session, EventPhotoModel.event_id==db_event.id)

            if count_photo >= 10:
                raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Photo limit exceeded")

            EventPhotoTasks.add_new_photos_task.delay(
                event_uuid=db_event.id,
                photos=photos
            )
            log.info("Photo upload started")


    @classmethod
    async def get_photos(cls, event_uuid: uuid.UUID, offset: int, limit: int) -> List[EventPhoto]:
        async with async_session_maker() as session:
            db_event = await EventDao.find_one_or_none(
                session,
                id=event_uuid
            )
            if not db_event:
                raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Event not found")

            db_photo = await EventPhotoDao.find_all(
                session,
                offset,
                limit,
                EventPhotoModel.event_id==db_event.id
            )
            log.debug("Photos fetched")
            return db_photo



    @classmethod
    async def delete_photo(cls, event_uuid: uuid.UUID, photo_uuid: uuid.UUID, user_id: uuid.UUID):
        async with async_session_maker() as session:
            db_event = await EventDao.find_one_or_none(
                session,
                id=event_uuid
            )
            if not db_event:
                raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Event not found")

            if db_event.user_id != user_id:
                raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Insufficient rights to modify the event")

            db_photo = await EventPhotoDao.find_one_or_none(session, id=photo_uuid)

            if db_photo is None:
                raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Photo not found")

            EventPhotoTasks.delete_photos_task.delay(photo_names=[db_photo.object_name])
            log.debug("Delete photo", extra={"photo_id": photo_uuid})


    @classmethod
    async def get_event(cls, event_uuid: uuid.UUID) -> Event:
        async with async_session_maker() as session:
            db_event = await EventDao.find_one_or_none(session, id=event_uuid)

            if db_event is None:
                log.warning("Event not found", extra={"event_id": str(event_uuid)})
                raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Event not found")

            log.debug("Event fetched", extra={"event_id": str(event_uuid)})
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

            log.debug("Events fetched", extra={"count": len(db_events), "offset": offset, "limit": limit})
            return db_events


    @classmethod
    async def update_event(cls, event_uuid: uuid.UUID, new_event: EventUpdate, user_id: uuid.UUID) -> Event:
        async with async_session_maker() as session:
            db_event = await EventDao.find_one_or_none(session, id=event_uuid)

            if db_event is None:
                log.warning("Event not found for update", extra={"event_id": str(event_uuid)})
                raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Event not found")

            if db_event.user_id != user_id:
                log.warning("User does not have permission to update event", extra={"event_id": str(event_uuid), "user_id": str(user_id)})
                raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Insufficient rights to modify the event")

            update_event = await EventDao.update(
                session,
                EventModel.id == event_uuid,
                obj_in=EventUpdateDB(
                    **new_event.model_dump()
                )
            )

            await session.commit()
            log.info("Event updated", extra={"event_id": str(event_uuid), "user_id": str(user_id)})
            return update_event


    @classmethod
    async def delete_event(cls, event_uuid: uuid.UUID, user_id: uuid.UUID) -> None:
        async with async_session_maker() as session:
            db_event = await EventDao.find_one_or_none(session, id=event_uuid, user_id=user_id)

            if db_event is None:
                log.warning("Event not found for deletion", extra={"event_id": str(event_uuid), "user_id": str(user_id)})
                raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Event not found")

            db_photos = await EventPhotoDao.find_all(session, 0, None, EventPhotoModel.event_id==db_event.id)

            photo_names = [photo.object_name for photo in db_photos]

            EventPhotoTasks.delete_photos_task.delay(photo_names=photo_names)

            await EventDao.delete(session, id=db_event.id)
            await session.commit()
            log.info("Event deleted", extra={"event_id": str(event_uuid), "user_id": str(user_id), "photos_count": len(photo_names)})


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
                log.warning("Review already exists", extra={"user_id": str(user_id), "event_id": str(event_id)})
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
            log.info("Review created", extra={"user_id": str(user_id), "event_id": str(event_id), "rating": new_review.rating})
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
        log.debug("Reviews fetched", extra={"count": len(db_reviews), "user_id": str(user_id) if user_id else None, "event_id": str(event_id) if event_id else None})
        return db_reviews


    @classmethod
    async def put_review(cls, user_id: uuid.UUID, event_id: uuid.UUID, edit_event: EventReviewsUpdate) -> EventReviews:
        async with async_session_maker() as session:
            db_event = await EventReviewsDao.find_one_or_none(session, user_id=user_id, event_id=event_id)

            if not db_event:
                log.warning("Review not found for update", extra={"user_id": str(user_id), "event_id": str(event_id)})
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
            log.info("Review updated", extra={"user_id": str(user_id), "event_id": str(event_id), "rating": edit_event.rating})
        return db_edit_event


    @classmethod
    async def delete_review(cls, user_id: uuid.UUID, event_id: uuid.UUID):
        async with async_session_maker() as session:
            db_event = await EventReviewsDao.find_one_or_none(session, user_id=user_id, event_id=event_id)

            if not db_event:
                log.warning("Review not found for deletion", extra={"user_id": str(user_id), "event_id": str(event_id)})
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
            log.info("Review deleted", extra={"user_id": str(user_id), "event_id": str(event_id)})