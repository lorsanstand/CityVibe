import uuid
from typing import Optional

from pydantic import BaseModel, Field


class RefreshSessionCreate(BaseModel):
    refresh_token: uuid.UUID
    expires_in: int
    user_id: uuid.UUID


class RefreshSessionUpdate(RefreshSessionCreate):
    user_id: Optional[uuid.UUID] = Field(None)
    

class Token(BaseModel):
    access_token: str
    refresh_token: uuid.UUID
    token_type: str