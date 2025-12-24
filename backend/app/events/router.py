import uuid
import io
import logging
from PIL import Image
from typing import List

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status

from app.events.schemas import EventCreate, Event, EventUpdate, EventSearch
from app.events.schemas import EventReviews, EventReviewsCreate, EventReviewsUpdate
from app.events.schemas import EventPhoto
from app.events.service import EventService, EventReviewsService
from app.users.models import UserModel
from app.auth.dependencies import get_current_active_user, get_current_organizer

log = logging.getLogger(__name__)

router = APIRouter(prefix="/events", tags=['events'])


@router.post("/")
async def create_event(
        event: EventCreate,
        user: UserModel = Depends(get_current_organizer),
) -> Event:
    log.info("Event creation started", extra={"user_id": str(user.id), "event_name": event.name})
    return await EventService.create_new_event(user.id, event)


@router.get("/{event_id}/photo")
async def get_photos(event_id: uuid.UUID, offset: int, limit: int) -> List[EventPhoto]:
    return await EventService.get_photos(event_id, offset, limit)


@router.post("/{event_id}/photo")
async def upload_photo(
        event_id: uuid.UUID,
        photos: List[UploadFile] = File(...),
        user: UserModel = Depends(get_current_organizer)
):
    log.info("Photo upload started", extra={"event_id": str(event_id), "user_id": str(user.id), "count": len(photos)})
    photo_list = []

    if len(photos) > 10:
        log.warning("Photo limit exceeded", extra={"event_id": str(event_id), "count": len(photos)})
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Photo limit exceeded")
    for photo in photos:
        if not photo.content_type.startswith("image/"):
            log.warning("Invalid file type for photo", extra={"event_id": str(event_id), "content_type": photo.content_type})
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="The file must be in photo format.")

        if photo.size > 15 * 1024 * 1024:
            log.warning("Photo size exceeds limit", extra={"event_id": str(event_id), "size": photo.size})
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="The size must be no more than 15 MB")

        image = Image.open(io.BytesIO(await photo.read()))
        if image.width >= 4096 or image.height >= 4096 or image.width != image.height:
            log.warning("Photo dimensions invalid", extra={"event_id": str(event_id), "width": image.width, "height": image.height})
            raise  HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="The photo must be no more than 4096 pixels in resolution and 1:1 format."
            )

        png_bytes = io.BytesIO()
        image.convert("RGBA").save(png_bytes, format="PNG")
        png_bytes.seek(0)
        photo_list.append(png_bytes.getvalue())

    await EventService.upload_photo(event_id, photo_list, user.id)

    return {"message": "Photos uploaded successfully"}


@router.delete("/{event_id}/photo")
async def delete_photo(
        event_id: uuid.UUID,
        photo_id: uuid.UUID,
        user: UserModel = Depends(get_current_organizer)
):
    log.info("Photo deletion started", extra={"event_id": str(event_id), "photo_id": str(photo_id), "user_id": str(user.id)})
    await EventService.delete_photo(event_id, photo_id, user.id)
    return {"message": "The photo was successfully deleted"}


@router.get("/{event_id}")
async def get_event(event_id: uuid.UUID) -> Event:
    return await EventService.get_event(event_uuid=event_id)


@router.post("/search")
async def get_events(
        offset: int,
        limit: int,
        event: EventSearch
) -> List[Event]:
    log.debug("Search events", extra={"offset": offset, "limit": limit, "search_params": event.model_dump(exclude_none=True)})
    return await EventService.get_events(event, offset, limit)


@router.put("/{event_id}")
async def update_event(
        event_id: uuid.UUID,
        event: EventUpdate,
        user: UserModel = Depends(get_current_organizer)
) -> Event:
    log.info("Event update started", extra={"event_id": str(event_id), "user_id": str(user.id)})
    return await EventService.update_event(event_id, event, user.id)


@router.delete("/{event_id}")
async def delete_event(
        event_id: uuid.UUID,
        user: UserModel = Depends(get_current_organizer)
) -> dict:
    log.info("Event deletion started", extra={"event_id": str(event_id), "user_id": str(user.id)})
    await EventService.delete_event(event_id, user.id)
    return {"message": "The event was successfully deleted"}


@router.get("/{event_id}/reviews")
async def get_reviews(event_id: uuid.UUID, offset: int, limit: int):
    log.debug("Getting event reviews", extra={"event_id": str(event_id), "offset": offset, "limit": limit})
    return await EventReviewsService.get_reviews(offset, limit, event_id=event_id)


@router.post("/{event_id}/reviews")
async def create_review(
        event_id: uuid.UUID,
        new_review: EventReviewsCreate,
        user: UserModel = Depends(get_current_active_user)
) -> EventReviews:
    log.info("Review creation started", extra={"event_id": str(event_id), "user_id": str(user.id), "rating": new_review.rating})
    return await EventReviewsService.create_new_review(user.id, event_id, new_review)


@router.put("/{event_id}/reviews")
async def edit_review(
        event_id: uuid.UUID,
        review: EventReviewsUpdate,
        user: UserModel = Depends(get_current_active_user)
):
    log.info("Review update started", extra={"event_id": str(event_id), "user_id": str(user.id), "rating": review.rating})
    return await EventReviewsService.put_review(user.id, event_id, review)


@router.delete("/{event_id}/reviews")
async def delete_review(
        event_id: uuid.UUID,
        user: UserModel = Depends(get_current_active_user)
) -> dict:
    log.info("Review deletion started", extra={"event_id": str(event_id), "user_id": str(user.id)})
    await EventReviewsService.delete_review(user.id, event_id)
    return {"message": "The review was successfully deleted"}