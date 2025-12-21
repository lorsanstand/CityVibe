from datetime import datetime

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import  DeclarativeBase, Mapped, mapped_column
from sqlalchemy import  MetaData, NullPool, func

from app.config import settings
from app.constants import DB_NAMING_CONVENTION


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=DB_NAMING_CONVENTION)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())


if settings.MODE == "TEST":
    DATABASE_URL = settings.TEST_DATABASE_URL
    DATABASE_PARAMS = {"poolclass": NullPool}
else:
    DATABASE_URL = settings.DATABASE_URL
    DATABASE_PARAMS = {}

engine = create_async_engine(DATABASE_URL, **DATABASE_PARAMS)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)