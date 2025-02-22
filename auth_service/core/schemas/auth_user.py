from pydantic import BaseModel, EmailStr
from typing import Optional


class AuthUser(BaseModel):
    user_id: int
    username: str
    password: bytes
    email: EmailStr | None = None
    is_active: bool = True
    refresh_token: Optional[str]
