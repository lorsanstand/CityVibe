import uuid
import io
from PIL import Image
from typing import List

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status

from app.events.schemas import EventCreate, Event, EventUpdate
from app.events.service import EventService
from app.users.schemas import User
from app.auth.dependencies import get_current_active_user

router = APIRouter(prefix="/events", tags=['events'])


@router.post("/")
async def create_event(
        event: EventCreate,
        user: User = Depends(get_current_active_user),
) -> Event:
    return await EventService.create_new_event(user.id, event)


@router.post("/{event_id}/photo")
async def upload_photo(
        event_id: uuid.UUID,
        photos: List[UploadFile] = File(...),
        user: User = Depends(get_current_active_user)
) -> List[str]:
    photo_list = []

    for photo in photos:
        if not photo.content_type.startswith("image/"):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="The file must be in photo format.")

        if photo.size > 15 * 1024 * 1024:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="The size must be no more than 15 MB")

        image = Image.open(io.BytesIO(await photo.read()))
        if image.width >= 4096 or image.height >= 4096 or image.width != image.height:
            raise  HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="The photo must be no more than 4096 pixels in resolution and 1:1 format."
            )

        png_bytes = io.BytesIO()
        image.convert("RGBA").save(png_bytes, format="PNG")
        png_bytes.seek(0)
        photo_list.append(png_bytes.getvalue())

    return await EventService.upload_photo(event_id, photo_list, user.id)


@router.get("/{event_id}")
async def get_event(event_id: uuid.UUID) -> Event:
    return await EventService.get_event(event_uuid=event_id)


@router.put("/{event_id}")
async def update_event(
        event_id: uuid.UUID,
        event: EventUpdate,
        user: User = Depends(get_current_active_user)
) -> Event:
    return await EventService.update_event(event_id, event, user.id)

@router.delete("/{event_id}")
async def delete_event(
        event_id: uuid.UUID,
        user: User = Depends(get_current_active_user)
) -> dict:
    await EventService.delete_event(event_id, user.id)
    return {"message": "The event was successfully deleted"}