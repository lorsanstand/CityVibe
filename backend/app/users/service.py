import uuid
from typing import List

from fastapi import HTTPException, status

from app.auth.utils import get_hashed_password
from app.users.schemas import UserCreate, UserCreateDB, UserUpdateDB, UserUpdate, User
from app.users.models import UserModel
from app.users.dao import UserDao
from app.database import async_session_maker



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
            return db_user


    @classmethod
    async def get_user(cls, user_id: uuid.UUID) -> User:
        async with async_session_maker() as session:
            db_user = await UserDao.find_one_or_none(session, id=user_id)
            if db_user is None:
                raise HTTPException(status.HTTP_404_NOT_FOUND, detail="user not found")
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
            return user_update


    @classmethod
    async def delete_user(cls, user_id: uuid.UUID):
        async with async_session_maker() as session:
            db_user = await UserDao.find_one_or_none(session, id=user_id)
            if db_user is None:
                raise HTTPException(status.HTTP_404_NOT_FOUND, detail="user not found")
            await  UserDao.update(
                session,
                UserModel.id == user_id,
                obj_in={"is_active": False}
            )
            await session.commit()


    @classmethod
    async def get_users_list(cls, *filter, offset: int = 0, limit: int = 100, **filter_by) -> List[UserModel]:
        async with async_session_maker() as session:
            users = await UserDao.find_all(session, offset, limit, *filter, **filter_by)
        if users is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Users not found")
        return users


    @classmethod
    async def update_user_from_superuser(cls, user_id: uuid.UUID, user: UserUpdate) -> UserModel:
        async with async_session_maker() as session:
            db_user = await UserDao.find_one_or_none(session, UserModel.id == user_id)
            if db_user is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

            user_in = UserUpdateDB(**user.model_dump(exclude_unset=True))
            user_update = await UserDao.update(
                session,
                UserModel.id == user_id,
                obj_in=user_in)
            await session.commit()
            return user_update

    @classmethod
    async def delete_user_from_superuser(cls, user_id: uuid.UUID):
        async with async_session_maker() as session:
            await UserDao.delete(session, UserModel.id == user_id)
            await session.commit()