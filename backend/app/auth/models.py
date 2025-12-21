import uuid
from datetime import  datetime

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import TIMESTAMP, ForeignKey
from sqlalchemy.sql import func

from app.database import Base

class RefreshSessionModel(Base):
    __tablename__ = 'refresh_session'

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    refresh_token: Mapped[uuid.UUID] = mapped_column(UUID, index=True)
    expires_in: Mapped[int]
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())

    user_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("user.id", ondelete="CASCADE"))