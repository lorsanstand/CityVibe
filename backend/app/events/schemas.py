import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict

from app.events.models import EventEnvironment

class EventBase(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=20)
    description: Optional[str] = Field(None, min_length=4, max_length=200)
    address: Optional[str] = Field(None)
    latitude: Optional[float] = Field(None)
    longitude: Optional[float] = Field(None)
    capacity: Optional[int] = Field(None, ge=1, le=200)
    environment: Optional[EventEnvironment] = Field(None)
    start: Optional[datetime] = Field(None)
    end: Optional[datetime] = Field(None)
    age_rating: Optional[int] = Field(None, ge=1, le=18)
    is_active: Optional[bool] = Field(None)


class EventCreate(EventBase):
    name: str = Field(..., min_length=3, max_length=20)
    description: str = Field(..., min_length=4, max_length=200)
    address: str = Field(...)
    latitude: float = Field(...)
    longitude: float = Field(...)
    capacity: int = Field(..., ge=1, le=200)
    environment: EventEnvironment = Field(...)
    start: datetime = Field(...)
    end: datetime = Field(...)
    age_rating: int = Field(..., ge=1, le=18)
    is_active: bool = Field(True)


    model_config = ConfigDict(from_attributes=True)
    
    
class EventCreateDB(EventBase):
    user_id: Optional[uuid.UUID] = Field(None)
    photo_path: Optional[list] = Field(None)
    
class EventUpdateDB(EventBase):
    pass
    photo_path: Optional[list] = Field(None)


class EventUpdate(EventBase):
    pass
    photo_path: Optional[list] = Field(None)


class Event(EventCreate):
    id: uuid.UUID
    user_id: uuid.UUID
    photo_path: Optional[list] = Field(None)