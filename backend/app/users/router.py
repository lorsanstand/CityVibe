import uuid
from typing import List

from fastapi import APIRouter, Depends, Response

from app.auth.dependencies import get_current_active_user, get_current_superuser
from app.auth.service import AuthService
from app.users.service import UserService
from app.users.schemas import User, UserUpdate
from app.users.models import UserModel

router = APIRouter(prefix="/users", tags=["users"])

@router.get("")
async def get_users_list(
        offset: int = 0,
        limit: int = 100,
        current_user = Depends(get_current_active_user)
) -> List[User]:
    users_list = await UserService.get_users_list(offset=offset, limit=limit)
    return users_list


@router.get("/me")
async def get_current_user(current_user: UserModel = Depends(get_current_active_user)) -> User:
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
    await UserService.delete_user_from_superuser(user_id)
    return {"message": "User was deleted"}