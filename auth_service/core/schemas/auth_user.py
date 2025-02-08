from pydantic import BaseModel, EmailStr


class AuthUser(BaseModel):
    username: str
    email: EmailStr | None = None
    active: bool = True
