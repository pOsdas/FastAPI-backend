from datetime import datetime

from pydantic import BaseModel, EmailStr
from typing import Optional


class AuthUser(BaseModel):
    user_id: int
    password: bytes
    refresh_token: Optional[str] = None
    updated_at: Optional[datetime] = None


class RegisterUserSchema(BaseModel):
    username: str
    password: str
    email: EmailStr


class CombinedUserSchema(BaseModel):
    user_id: int
    email: EmailStr
