from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import NullPool

from app.config import settings

if settings.MODE == "TEST":
    DATABASE_URL = settings.TEST_DATABASE_URL
    DATABASE_PARAMS = {"poolclass": NullPool}
else:
    DATABASE_URL = settings.DATABASE_URL
    DATABASE_PARAMS = {}

_celery_engine = None
_celery_async_session_maker = None


def get_celery_engine():
    global _celery_engine
    if _celery_engine is None:
        _celery_engine = create_async_engine(DATABASE_URL, **DATABASE_PARAMS)
    return _celery_engine


def get_celery_async_session_maker():
    global _celery_async_session_maker
    if _celery_async_session_maker is None:
        _celery_async_session_maker = async_sessionmaker(
            get_celery_engine(), 
            expire_on_commit=False, 
            class_=AsyncSession
        )
    return _celery_async_session_maker


def reset_celery_db():
    global _celery_engine, _celery_async_session_maker
    _celery_engine = None
    _celery_async_session_maker = None


celery_async_session_maker = None
