import uuid
import logging
from typing import List

from fastapi import APIRouter, Depends, Response

from app.auth.dependencies import get_current_active_user, get_current_superuser
from app.auth.service import AuthService
from app.users.service import UserService, UserEventFavoritesService
from app.users.schemas import User, UserUpdate, UserEventFavoritesCreate, UserEventFavorites
from app.users.models import UserModel

log = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/")
async def get_users_list(
        offset: int = 0,
        limit: int = 100,
        current_superuser_user: UserModel = Depends(get_current_superuser)
) -> List[User]:
    log.info("Getting users list", extra={"offset": offset, "limit": limit})
    users_list = await UserService.get_users_list(offset=offset, limit=limit)
    return users_list


@router.get("/me")
async def get_current_user(current_user: UserModel = Depends(get_current_active_user)) -> User:
    log.debug("Getting current user profile", extra={"user_id": str(current_user.id)})
    return current_user


@router.put("/me")
async def put_current_user(
        user: UserUpdate,
        current_user: UserModel = Depends(get_current_active_user)
) -> User:
    return await UserService.update_user(current_user.id, user)


@router.delete("/me")
async def delete_current_user(
        response: Response,
        current_user: UserModel = Depends(get_current_active_user)
):
    log.info("User deleting their account", extra={"user_id": str(current_user.id), "email": current_user.email})
    response.delete_cookie('access_token')
    response.delete_cookie('refresh_token')

    await AuthService.abort_all_sessions(current_user.id)
    await UserService.delete_user(current_user.id)
    return {"message": "User status is not active already"}


@router.get("/{user_id}")
async def get_user(
        user_id: uuid.UUID,
        current_user: UserModel = Depends(get_current_superuser)
) -> User:
    log.info("Superuser accessing user profile", extra={"target_user_id": str(user_id), "superuser_id": str(current_user.id)})
    return await UserService.get_user(user_id)

@router.put("/{user_id}")
async def update_user(
    user_id: uuid.UUID,
    user: User,
    current_user: UserModel = Depends(get_current_superuser)
) -> User:
    return await UserService.update_user_from_superuser(user_id, user)


@router.delete("/{user_id}")
async def delete_user(
    user_id: uuid.UUID,
    current_user: UserModel = Depends(get_current_superuser)
):
    log.info("Superuser deleting user", extra={"user_id": str(user_id), "superuser_id": str(current_user.id)})
    await UserService.delete_user_from_superuser(user_id)
    return {"message": "User was deleted"}


@router.post("/me/favorites")
async def add_new_favorite(
        event: UserEventFavoritesCreate,
        current_user: UserModel = Depends(get_current_active_user)
) -> UserEventFavorites:
    return await UserEventFavoritesService.add_new_favorite(current_user.id, event.event_id)


@router.get("/me/favorites")
async def get_favorites(
        offset: int,
        limit: int,
        current_user: UserModel = Depends(get_current_active_user),
) -> List[UserEventFavorites]:
    return await UserEventFavoritesService.get_favorites(current_user.id, offset, limit)


@router.delete("/me/favorites{event_id}")
async def delete_favorite(
        event_id: uuid.UUID,
        current_user: UserModel = Depends(get_current_active_user)
) -> dict:
    await UserEventFavoritesService.delete_favorite(current_user.id, event_id)
    return {"message": "The favorites was successfully deleted"}