from fastapi import (
    APIRouter, Depends,
    HTTPException, status,
)
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import (
    OAuth2PasswordBearer, OAuth2PasswordRequestForm
)
from pydantic import BaseModel
from typing import Annotated


from .utils.helpers import (
    create_access_token,
    create_refresh_token,
)
from .validation import (
    get_auth_user_from_token_of_type,
    REFRESH_TOKEN_TYPE,
)
from auth_service.core.schemas import (
    CombinedUserSchema
)
from auth_service.core import security
from auth_service.core.logger import logger
from auth_service.core.models import db_helper
from auth_service.core.models import AuthUser as AuthUserModel
from auth_service.crud.users_crud import get_user_service_user_by_username

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/jwt/login/")


class TokenInfo(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "Bearer"


router = APIRouter(
    prefix="/jwt",
    tags=["JWT"],
    # dependencies=[Depends(oauth2_scheme)]
)


async def validate_auth_user(
        session: Annotated[
            AsyncSession,
            Depends(db_helper.session_getter)
        ],
        username: str,
        password: str,
):
    logger.info(f"Received data: {username}, {password}")
    unauthed_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid username or password"
    )

    # Запрос на поиск
    try:
        response = await get_user_service_user_by_username(username=username)
    except Exception as e:
        raise e

    user_profile = response.json()
    user_id = user_profile.get("user_id")
    active_status = user_profile.get("is_active")

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


# login via jwt
@router.post("/login/", response_model=TokenInfo)
async def auth_user_issue_jwt(
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
        session: AsyncSession = Depends(db_helper.session_getter),
):
    """
    Допустим что при регистрации не выдаются токены
    """
    try:
        user = await validate_auth_user(
            session=session,
            username=form_data.username,
            password=form_data.password
        )
    except HTTPException as e:
        logger.error("Authentication failed: %s", e.detail)
        raise

    access_token = create_access_token(user.user_id, user.email)
    refresh_token = create_refresh_token(user.user_id, user.email)

    logger.info("Successfully created tokens for user %s", user.user_id)
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
    # Инвалидируем старый токен
    # await revoke_refresh_token(old_token)

    # Генерируем новые токены
    access_token = create_access_token(user.user_id, user.email)
    refresh_token = create_refresh_token(user.user_id, user.email)

    logger.info("Successfully refreshed tokens for user %s", user.user_id)
    return TokenInfo(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="Bearer"
    )
