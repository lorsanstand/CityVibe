import uuid
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import HTTPException, status

from app.auth.utils import is_valid_password
from app.auth.schemas import Token, RefreshSessionCreate, RefreshSessionUpdate
from app.auth.models import RefreshSessionModel
from app.auth.dao import  RefreshSessionDAO

from app.users.models import UserModel
from app.users.dao import UserDao

from app.database import  async_session_maker
from app.config import settings
from app.exceptions import InvalidTokenException, TokenExpiredException

log = logging.getLogger(__name__)

class AuthService:
    @classmethod
    async def create_token(cls, user_id: uuid.UUID) -> Token:
        access_token = cls._create_access_token(user_id)
        refresh_token_expires = timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        refresh_token = cls._create_refresh_token()

        async with async_session_maker() as session:
            await RefreshSessionDAO.add(
                session,
                RefreshSessionCreate(
                    user_id=user_id,
                    refresh_token=refresh_token,
                    expires_in=refresh_token_expires.total_seconds()
                )
            )
            await session.commit()
        log.info("Token created for user", extra={"user_id": str(user_id)})
        return Token(access_token=access_token, refresh_token=refresh_token, token_type='bearer')


    @classmethod
    def create_verify_email_token(cls, user_id: uuid.UUID):
        return cls._create_verify_email_token(user_id)


    @classmethod
    async def verify_user(cls, token: str) -> UserModel:
        try:
            payload = jwt.decode(token, settings.SECRET, algorithms=settings.ALGORITHMS)
            user_id = payload.get("sub")
            expire_time =  payload.get("exp")

            if user_id is None:
                log.warning("Invalid token: user_id is None")
                raise InvalidTokenException

            if datetime.fromtimestamp(expire_time, timezone.utc) <= datetime.now(timezone.utc):
                log.warning("Token expired", extra={"user_id": user_id})
                raise TokenExpiredException

        except Exception as e:
            log.error(f"Token verification failed: {str(e)}")
            raise InvalidTokenException

        async with async_session_maker() as session:
            user = await UserDao.find_one_or_none(session, id=user_id)

            if user is None:
                log.error("User not found during verification", extra={"user_id": user_id})
                raise HTTPException(
                    status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )

            update_user = await UserDao.update(session, UserModel.id==user.id, obj_in={"is_verified": True})
            await session.commit()
            log.info("User verified", extra={"user_id": user_id})
            return update_user


    @classmethod
    async def abort_all_sessions(cls, user_id: uuid.UUID):
        async with async_session_maker() as session:
            await RefreshSessionDAO.delete(session, RefreshSessionModel.user_id == user_id)
            await session.commit()
        log.info("All sessions aborted for user", extra={"user_id": str(user_id)})


    @classmethod
    async def authenticate_user(cls, email: str, password: str) -> Optional[UserModel]:
        async with async_session_maker() as session:
            user = await UserDao.find_one_or_none(session, email=email)
        if user and is_valid_password(password, str(user.hashed_password)):
            log.info("User authenticated successfully", extra={"email": email})
            return user
        log.warning("Authentication failed", extra={"email": email})
        return None


    @classmethod
    async def refresh_token(cls, token) -> Token:
        async with async_session_maker() as session:
            refresh_session = await RefreshSessionDAO.find_one_or_none(session, RefreshSessionModel.refresh_token == token)

            if refresh_session is None:
                log.warning("Refresh token not found")
                raise InvalidTokenException
            if datetime.now(timezone.utc) >= refresh_session.created_at + timedelta(seconds=refresh_session.expires_in):
                await RefreshSessionDAO.delete(id=refresh_session.id)
                log.warning("Refresh token expired", extra={"user_id": str(refresh_session.user_id)})
                raise TokenExpiredException

            user = await UserDao.find_one_or_none(session, id=refresh_session.user_id)
            if user is None:
                log.error("User not found during token refresh", extra={"user_id": str(refresh_session.user_id)})
                raise InvalidTokenException

            access_token = cls._create_access_token(user.id)
            refresh_token_expires = timedelta(
                days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
            refresh_token = cls._create_refresh_token()

            await RefreshSessionDAO.update(
                session,
                RefreshSessionModel.id == refresh_session.id,
                obj_in=RefreshSessionUpdate(
                    refresh_token=refresh_token,
                    expires_in=refresh_token_expires.total_seconds()
                )
            )
            await session.commit()
        log.info("Token refreshed for user", extra={"user_id": str(user.id)})
        return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer")


    @classmethod
    async def logout(cls, token) -> None:
        async with async_session_maker() as session:
            refresh_session = await RefreshSessionDAO.find_one_or_none(session, RefreshSessionModel.refresh_token == token)
            if refresh_session:
                await RefreshSessionDAO.delete(session, id=refresh_session.id)
                log.info("User logged out", extra={"user_id": str(refresh_session.user_id)})
            await session.commit()


    @classmethod
    def _create_access_token(cls, user_id: uuid.UUID) -> str:
        to_encode = {
            "sub": str(user_id),
            "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        }
        encoded_jwt = jwt.encode(to_encode, settings.SECRET, algorithm=settings.ALGORITHMS)
        return f'Bearer {encoded_jwt}'


    @classmethod
    def _create_verify_email_token(cls, user_id: uuid.UUID) -> str:
        to_encode = {
            "sub": str(user_id),
            "exp": datetime.now(timezone.utc) + timedelta(hours=settings.VERIFY_EMAIL_TOKEN_HOURS)
        }
        encoded_jwt = jwt.encode(to_encode, settings.SECRET, algorithm=settings.ALGORITHMS)
        return f'{encoded_jwt}'


    @classmethod
    def _create_refresh_token(cls) -> uuid.UUID:
        return uuid.uuid4()