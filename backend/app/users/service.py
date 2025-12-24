import uuid
from typing import List
import logging

from fastapi import HTTPException, status

from app.auth.utils import get_hashed_password
from app.users.schemas import UserCreate, UserCreateDB, UserUpdateDB, UserUpdate, User, UserEventFavoritesCreateDB, UserEventFavorites
from app.users.models import UserModel
from app.users.dao import UserDao, UserEventFavoritesDao
from app.database import async_session_maker

log = logging.getLogger(__name__)


class UserService:
    @classmethod
    async def register_new_user(cls, new_user: UserCreate) -> User:
        async with async_session_maker() as session:
            user_exist = await UserDao.find_one_or_none(session, email=new_user.email)

            if user_exist:
                raise HTTPException(status.HTTP_409_CONFLICT, "User already exists")

            db_user = await UserDao.add(
                session,
                UserCreateDB(
                    **new_user.model_dump(),
                    hashed_password=get_hashed_password(new_user.password),
                    is_superuser= False,
                    is_verified = False
                )
            )
            await session.commit()
            log.info("The user has registered", extra={"user_id": db_user.id, "email": db_user.email})
            return db_user


    @classmethod
    async def get_user(cls, user_id: uuid.UUID) -> User:
        async with async_session_maker() as session:
            db_user = await UserDao.find_one_or_none(session, id=user_id)
            if db_user is None:
                log.warning("User not found", extra={"user_id": str(user_id)})
                raise HTTPException(status.HTTP_404_NOT_FOUND, detail="user not found")
            log.debug("User fetched", extra={"user_id": str(db_user.id)})
            return User(
                id=db_user.id,
                email=db_user.email,
                username=db_user.username,
                is_verified=db_user.is_verified,
                is_active=db_user.is_active,
                is_superuser=db_user.is_superuser,
                is_organizer=db_user.is_organizer
            )



    @classmethod
    async def update_user(cls, user_id: uuid.UUID, user: UserUpdate) -> UserModel:
        async with async_session_maker() as session:
            db_user = await UserDao.find_one_or_none(session, id=user_id)
            if db_user is None:
                log.warning("User not found for update", extra={"user_id": str(user_id)})
                raise HTTPException(status.HTTP_404_NOT_FOUND, detail="user not found")

            if user.password:
                user_in = UserUpdateDB(
                    **user.model_dump(
                        exclude={'is_active', 'is_verified', 'is_superuser'},
                        exclude_unset=True
                    ),
                    hashed_password=get_hashed_password(user.password)
                )
            else:
                user_in = UserUpdateDB(**user.model_dump())
            user_update = await UserDao.update(
                session,
                UserModel.id == user_id,
                obj_in=user_in
            )
            await session.commit()
            log.info("User updated", extra={"user_id": str(user_update.id), "email": user_update.email})
            return user_update


    @classmethod
    async def delete_user(cls, user_id: uuid.UUID):
        async with async_session_maker() as session:
            db_user = await UserDao.find_one_or_none(session, id=user_id)
            if db_user is None:
                log.warning("User not found for deletion", extra={"user_id": str(user_id)})
                raise HTTPException(status.HTTP_404_NOT_FOUND, detail="user not found")
            await  UserDao.update(
                session,
                UserModel.id == user_id,
                obj_in={"is_active": False}
            )
            await session.commit()
            log.info("User is inactive", extra={"user_id": str(user_id), "email": db_user.email})


    @classmethod
    async def get_users_list(cls, *filter, offset: int = 0, limit: int = 100, **filter_by) -> List[UserModel]:
        async with async_session_maker() as session:
            users = await UserDao.find_all(session, offset, limit, *filter, **filter_by)
        if users is None:
            log.warning("Users not found")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Users not found")
        log.debug("Users fetched", extra={"count": len(users), "offset": offset, "limit": limit})
        return users


    @classmethod
    async def update_user_from_superuser(cls, user_id: uuid.UUID, user: UserUpdate) -> UserModel:
        async with async_session_maker() as session:
            db_user = await UserDao.find_one_or_none(session, UserModel.id == user_id)
            if db_user is None:
                log.warning("User not found for superuser update", extra={"user_id": str(user_id)})
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

            user_in = UserUpdateDB(**user.model_dump(exclude_unset=True))
            user_update = await UserDao.update(
                session,
                UserModel.id == user_id,
                obj_in=user_in)
            await session.commit()
            log.info("User updated by superuser", extra={"user_id": str(user_update.id), "email": user_update.email})
            return user_update

    @classmethod
    async def delete_user_from_superuser(cls, user_id: uuid.UUID):
        async with async_session_maker() as session:
            db_user = await UserDao.find_one_or_none(session, id=user_id)
            if db_user is None:
                log.warning("User not found for superuser deletion", extra={"user_id": str(user_id)})
            else:
                await UserDao.delete(session, UserModel.id == user_id)
                log.info("User deleted by superuser", extra={"user_id": str(user_id), "email": db_user.email})
            await session.commit()


class UserEventFavoritesService:
    @classmethod
    async def add_new_favorite(cls, user_id: uuid.UUID, event_id: uuid.UUID) -> UserEventFavorites:
        async with async_session_maker() as session:
            favorite_exist = await UserEventFavoritesDao.find_one_or_none(session, user_id=user_id, event_id=event_id)

            if favorite_exist:
                log.warning("Event already in favorites", extra={"user_id": str(user_id), "event_id": str(event_id)})
                raise HTTPException(status.HTTP_409_CONFLICT, "The event has already been added to favorites")

            db_favorites = await UserEventFavoritesDao.add(
                session,
                obj_in={
                    "user_id": user_id,
                    "event_id": event_id
                }
            )
            await session.commit()
        log.debug("Added to favorite", extra={"user_id": str(user_id), "event_id": str(event_id)})
        return db_favorites


    @classmethod
    async def get_favorites(cls, user_id: uuid.UUID, offset: int = 0, limit: int = 10) -> List[UserEventFavorites]:
        async with async_session_maker() as session:
            db_favorites = await UserEventFavoritesDao.find_all(session, offset, limit, user_id=user_id)
        log.debug("Favorites fetched", extra={"number_favorites": len(db_favorites)})
        return db_favorites


    @classmethod
    async def delete_favorite(cls, user_id: uuid.UUID, event_id: uuid.UUID):
        async with async_session_maker() as session:
            await UserEventFavoritesDao.delete(session, user_id=user_id, event_id=event_id)
            await session.commit()
        log.debug("Favorite deleted", extra={"user_id": str(user_id), "event_id": str(event_id)})