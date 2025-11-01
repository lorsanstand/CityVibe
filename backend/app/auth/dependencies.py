from typing import Optional
import uuid

from fastapi import Depends, HTTPException, status
import jwt

from app.auth.utils import OAuth2PasswordBearerWithCookie
from app.config import settings
from app.users.models import UserModel
from app.users.service import UserService
from app.exceptions import InvalidTokenException


oauth2_scheme = OAuth2PasswordBearerWithCookie(tokenUrl="/api/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> Optional[UserModel]:
    try:
        payload = jwt.decode(token, settings.SECRET, algorithms=settings.ALGORITHMS)
        user_id = payload.get("sub")

        if user_id is None:
            raise InvalidTokenException

    except Exception:
        raise InvalidTokenException
    current_user = await UserService.get_user(uuid.UUID(user_id))

    if not current_user.is_verified:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="verify email")

    return current_user


async def get_current_superuser(current_user: UserModel = Depends(get_current_user)) -> UserModel:
    if not current_user.is_superuser:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Not enough privileges")
    return current_user


async def get_current_active_user(current_user: UserModel = Depends(get_current_user)) -> UserModel:
    if not current_user.is_active:
        raise  HTTPException(status.HTTP_403_FORBIDDEN, detail="User is not active")
    return current_user