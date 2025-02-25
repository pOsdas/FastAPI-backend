from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Annotated, Optional
from annotated_types import MinLen, MaxLen
from datetime import datetime


class CreateUser(BaseModel):
    username: Annotated[str, MinLen(3), MaxLen(32)]
    email: EmailStr


class ReadUser(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    username: str
    email: EmailStr


class UserSchema(BaseModel):
    model_config = ConfigDict(strict=True, from_attributes=True)

    id: int
    username: str
    email: EmailStr | None = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime


class UserUpdateSchema(BaseModel):
    new_name: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
