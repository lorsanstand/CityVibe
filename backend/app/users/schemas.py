import uuid
from typing import Optional

from pydantic import BaseModel, Field, EmailStr, ConfigDict


class UserBase(BaseModel):
    email: Optional[str] = Field(None)
    username: Optional[str] = Field(None)
    is_active: Optional[bool] = Field(True)
    is_verified: Optional[bool] = Field(False)
    is_superuser: Optional[bool] = Field(False)
    is_organizer: Optional[bool] = Field(False)


class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=20)
    password: str = Field(..., min_length=6, max_length=20)


class UserUpdate(UserBase):
    password: Optional[str] = None


class User(UserBase):
    id: uuid.UUID
    email: str
    username: str
    is_active: bool
    is_verified: bool
    is_superuser: bool
    is_organizer: bool

    model_config = ConfigDict(from_attributes=True)


class UserCreateDB(UserBase):
    hashed_password: Optional[str] = None


class UserUpdateDB(UserBase):
    hashed_password: str