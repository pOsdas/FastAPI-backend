import httpx
from fastapi import (
    APIRouter, Depends, Form,
    HTTPException, status
)
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import (
    HTTPBearer
)
from pydantic import BaseModel
from typing import Annotated


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
from auth_service.core.schemas import (
    AuthUser as AuthUserSchema,
    RegisterUserSchema, CombinedUserSchema
)
from auth_service.core import security
from auth_service.core.models import db_helper
from auth_service.core.config import settings
from auth_service.core.models import AuthUser as AuthUserModel

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


async def validate_auth_user(
        session: Annotated[
                    AsyncSession,
                    Depends(db_helper.session_getter)
                ],
        username: str = Form(...),
        password: str = Form(...),
):
    unauthed_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid username or password"
    )

    # Запрос на поиск
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{settings.user_service_url}/api/v1/users/username/{username}",
        )

    if response.status_code != status.HTTP_200_OK:
        raise unauthed_exc

    user_profile = response.json()
    user_id = user_profile.get("id")
    active_status = user_profile.get("is_active")
    print(f"validate_auth_user: {user_id}, {active_status}")

    # Активный ли пользователь
    if not active_status:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )

    # Проверка на наличие в auth_service
    stmt = select(AuthUserModel).where(AuthUserModel.user_id == user_id)
    result = await session.execute(stmt)
    auth_user = result.scalar_one_or_none()
    if not auth_user:
        return unauthed_exc

    if not security.validate_password(
        password=password,
        hashed_password=auth_user.password,
    ):
        raise unauthed_exc

    combined_data = CombinedUserSchema(
        user_id=int(user_id),
        email=user_profile.get("email"),
    )

    return combined_data


def get_current_active_auth_user(
        user: AuthUserModel = Depends(get_current_auth_user),
):
    if user.active:
        return user
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Inactive user"
    )


@router.post("/login/", response_model=TokenInfo)
def auth_user_issue_jwt(
        user: CombinedUserSchema = Depends(validate_auth_user)
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
        user: CombinedUserSchema = Depends(get_auth_user_from_token_of_type(REFRESH_TOKEN_TYPE))
):
    access_token = create_access_token(user)
    return TokenInfo(
        access_token=access_token,
    )