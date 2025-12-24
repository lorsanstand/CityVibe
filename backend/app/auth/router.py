import logging
from fastapi import APIRouter, Depends, Request, Response, status, BackgroundTasks
from fastapi.security import  OAuth2PasswordRequestForm

from app.auth.service import AuthService
from app.auth.schemas import Token
from app.auth.dependencies import get_current_active_user
from app.users.models import UserModel
from app.users.service import UserService
from app.users.schemas import User, UserCreate
from app.tasks.email_tasks import send_verify_email_task

from app.exceptions import InvalidCredentialsException
from app.config import settings

log = logging.getLogger(__name__)

router = APIRouter(prefix='/auth', tags=['auth'])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate) -> User:
    log.info("User registration started", extra={"email": user.email})
    db_user = await UserService.register_new_user(user)
    token = AuthService.create_verify_email_token(user_id=db_user.id)
    send_verify_email_task.delay(
        email=db_user.email,
        username=db_user.username,
        url=f"{settings.URL}/verify?token={token}"
    )
    log.info("Registration email sent", extra={"email": db_user.email, "user_id": str(db_user.id)})
    return db_user



@router.post("/login")
async def login(response:Response, credentials: OAuth2PasswordRequestForm = Depends()) -> Token:
    user = await AuthService.authenticate_user(credentials.username, credentials.password)
    if not user:
        log.warning("Failed login attempt", extra={"email": credentials.username})
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
    log.info("User logged in", extra={"email": credentials.username, "user_id": str(user.id)})
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
    log.info("User logged out", extra={"user_id": str(user.id)})
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
    log.debug("Token refreshed via endpoint")
    return new_token


@router.post("/verify")
async def verify_user(token: str):
    await AuthService.verify_user(token)
    log.info("Email verified successfully via token")
    return {"message": "email confirmed"}


@router.post("/abort")
async def abort_all_sessions(response: Response, user: UserModel = Depends(get_current_active_user)):
    response.delete_cookie("refresh_token")
    response.delete_cookie("access_token")

    await AuthService.abort_all_sessions(user.id)
    return {"message": "All sessions was aborted"}