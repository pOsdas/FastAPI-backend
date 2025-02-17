from fastapi import (
    APIRouter, Depends, Form,
    HTTPException, status
)
from fastapi.security import (
    HTTPBearer
)
from pydantic import BaseModel

from .utils.helpers import (
    create_access_token,
    create_refresh_token,
)
from .validation import (
    get_current_auth_user,
    get_auth_user_from_token_of_type,
    REFRESH_TOKEN_TYPE,
)
from auth_service.crud.crud import users_db
from auth_service.core.schemas import AuthUser
from auth_service.core import security

http_bearer = HTTPBearer(auto_error=False)


class TokenInfo(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "Bearer"


router = APIRouter(
    prefix="/jwt",
    tags=["JWT"],
    dependencies=[Depends(http_bearer)]
)


def validate_auth_user(
        username: str = Form(),
        password: str = Form()
):
    unauthed_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid username or password"
    )
    if not (user := users_db.get(username)):
        raise unauthed_exc

    if not security.validate_password(
        password=password,
        hashed_password=user.password,
    ):
        raise unauthed_exc

    if not user.active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )

    return user


def get_current_active_auth_user(
        user: AuthUser = Depends(get_current_auth_user),
):
    if user.active:
        return user
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Inactive user"
    )


@router.post("/login/", response_model=TokenInfo)
def auth_user_issue_jwt(
        user: AuthUser = Depends(validate_auth_user)
):
    access_token = create_access_token(user)
    refresh_token = create_refresh_token(user)
    return TokenInfo(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="Bearer"
    )


@router.post(
    "/refresh/",
    response_model=TokenInfo,
    response_model_exclude_none=True,
)
def auth_refresh_jwt(
        user: AuthUser = Depends(get_auth_user_from_token_of_type(REFRESH_TOKEN_TYPE))
):
    access_token = create_access_token(user)
    return TokenInfo(
        access_token=access_token,
    )