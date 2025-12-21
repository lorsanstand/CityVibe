from app.database import async_session_maker
from app.users.dao import UserDao
from app.users.models import UserModel
from app.users.schemas import UserCreateDB
from app.auth.utils import get_hashed_password
import asyncio

from app.config import settings


async def init() -> None:
    async with async_session_maker() as session:
        super_user = await UserDao.find_one_or_none(session, UserModel.email==settings.FIRST_SUPERUSER_EMAIL)

        if super_user is None:
            await UserDao.add(
                session,
                UserCreateDB(
                    email=settings.FIRST_SUPERUSER_EMAIL,
                    hashed_password=get_hashed_password(settings.FIRST_SUPERUSER_PASS),
                    username="admin",
                    is_organizer=True,
                    is_active=True,
                    is_superuser=True,
                    is_verified=True
                )
            )
        await session.commit()


asyncio.run(init())