from typing import List, Optional
import uuid

from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.security import  OAuth2PasswordRequestForm

from auth.service import AuthService
from users.models import UserModel
from users.service import UserService
from users.schemas import User, UserCreate
from auth.schemas import Token
from auth.dependencies import get_current_active_user

from exceptions import InvalidCredentialsException
from config import settings

router = APIRouter(prefix='/auth', tags=['auth'])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate) -> User:
    return await UserService.register_new_user(user)


@router.post("/login")
async def login(response:Response, credentials: OAuth2PasswordRequestForm = Depends()) -> Token:
    user = await AuthService.authenticate_user(credentials.username, credentials.password)
    if not user:
        raise InvalidCredentialsException
    token = await AuthService.create_token(user.id)
    response.set_cookie(
        'access_token',
        token.access_token,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=True
    )
    response.set_cookie(
        'refresh_token',
        token.refresh_token,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 30 * 24 * 60,
        httponly=True
    )
    return token


@router.post("/logout")
async def logout(
        request: Request,
        response: Response,
        user = Depends(get_current_active_user)
):
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")

    await AuthService.logout(request.cookies.get("refresh_token"))
    return {"message": "Logged out successfully"}


@router.post("/refresh")
async def refresh_token(request: Request, response: Response) -> Token:
    new_token = await AuthService.refresh_token(request.cookies.get("refresh_token"))

    response.set_cookie(
        'access_token',
        new_token.access_token,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=True,
    )
    response.set_cookie(
        'refresh_token',
        new_token.refresh_token,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 30 * 24 * 60,
        httponly=True,
    )
    return new_token


@router.post("/verify")
async def verify_user(token: str):
    user = await AuthService.verify_user(token)
    return user


@router.post("/abort")
async def abort_all_sessions(response: Response, user: UserModel = Depends(get_current_active_user)):
    response.delete_cookie("refresh_token")
    response.delete_cookie("access_token")

    await AuthService.abort_all_sessions(user.id)
    return {"message": "All sessions was aborted"}