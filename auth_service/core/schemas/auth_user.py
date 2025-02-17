from pydantic import BaseModel, EmailStr


class AuthUser(BaseModel):
    username: str
    hashed_password: bytes
    refresh_token: str
    email: EmailStr | None = None
    active: bool = True
