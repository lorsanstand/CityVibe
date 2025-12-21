import uuid
from enum import Enum
from typing import List
from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey, ARRAY, String, TIMESTAMP

from app.database import Base


class EventEnvironment(str, Enum):
    indoor = "Закрытый"
    outdoor = "Открытый"
    semi_door = "Частично открытое"


class EventModel(Base):
    __tablename__ = "events"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, index=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(index=True)
    description: Mapped[str] = mapped_column()
    address: Mapped[str] = mapped_column(index=True)
    latitude: Mapped[float] = mapped_column(index=True)
    longitude: Mapped[float] = mapped_column(index=True)
    capacity: Mapped[int] = mapped_column(index=True)
    # photo_path: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=True)
    environment: Mapped[EventEnvironment] = mapped_column(index=True)
    start: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True),index=True)
    end: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), index=True)
    age_rating: Mapped[int] = mapped_column(index=True)
    average_rating: Mapped[float] = mapped_column(index=True, nullable=True)
    count_reviews: Mapped[int] = mapped_column(default=0)
    is_active: Mapped[bool] = mapped_column()

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"))


class EventReviewsModel(Base):
    __tablename__ = "events_reviews"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    content: Mapped[str] = mapped_column(nullable=False)
    rating: Mapped[int] = mapped_column(nullable=False)
    event_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), index=True)


class EventPhotoModel(Base):
    __tablename__ = "events_photo"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    url: Mapped[str] = mapped_column(nullable=False, unique=True)
    object_name: Mapped[str] = mapped_column(nullable=False, unique=True, index=True)
    event_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), index=True)