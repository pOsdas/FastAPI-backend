from typing import Annotated
import redis.asyncio as redis
import httpx
from fastapi import (
    APIRouter, Depends, HTTPException,
    status, Header,
)
from fastapi.security import (
    HTTPBasic, HTTPBasicCredentials,
    HTTPBearer, HTTPAuthorizationCredentials,
)
from sqlalchemy.ext.asyncio import AsyncSession

from auth_service.core.models import db_helper
from auth_service.core.redis_client import redis_client
from auth_service.core.models.auth_user import AuthUser as AuthUserModel
from auth_service.core.config import settings
from auth_service.core.security import verify_password, hash_password
from auth_service.core.schemas import RegisterUserSchema, TokenResponseSchema
from auth_service.core.schemas import AuthUser as AuthUserSchema
from auth_service.crud.tokens_crud import (
    get_username_by_static_auth_token, update_refresh_token,
)
from auth_service.crud.users_crud import (
    get_all_users, delete_auth_user, get_auth_user,
    create_user_service_user,
)
from auth_service.api.api_v1.utils.helpers import (
    create_access_token, create_refresh_token
)
from auth_service.core.logger import logger

router = APIRouter(prefix="/auth", tags=["AUTH"])

security = HTTPBasic()
bearer_scheme = HTTPBearer(auto_error=False)

# failed attempts
MAX_ATTEMPTS = 5
BLOCK_TIME_SECONDS = 300  # 5 минут


@router.get("/basic-auth/")
def demo_basic_auth_credentials(
        credentials: Annotated[HTTPBasicCredentials, Depends(security)],
):
    """
    Не для продакшена
    """
    return {
        "message": "Hi!",
        "username": credentials.username,
        "password": credentials.password,
    }


@router.post("/register")
async def register_user(
        user_data: RegisterUserSchema,
        session: Annotated[
                    AsyncSession,
                    Depends(db_helper.session_getter),
                ],
) -> TokenResponseSchema:
    # 1 Запрос на создание
    username = user_data.username
    email = user_data.email

    try:
        response = await create_user_service_user(username, email)
    except Exception as e:
        raise e

    user_profile = response.json()
    user_id = user_profile.get("user_id")
    if not user_id:
        logger.error("User profile creation error: no user_id returned")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User profile creation error: no user_id returned"
        )

    # 2 Хешируем пароль и создаем запись в auth_service
    hashed_pw = hash_password(user_data.password)
    new_auth_user = AuthUserModel(
        user_id=user_id,
        password=hashed_pw,
        refresh_token=None,
    )
    session.add(new_auth_user)
    try:
        await session.commit()
        await session.refresh(new_auth_user)
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    # 3 Генерируем новые токены
    refresh_token = create_refresh_token(user_id, email)
    access_token = create_access_token(user_id, email)

    # 4 Инвалидируем старый токен и прикрепляем новый
    await update_refresh_token(session, new_auth_user, refresh_token)

    logger.info(f"User created successfully")
    return TokenResponseSchema(
        user_id=user_id,
        username=username,
        email=email,
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.get("/get_users", response_model=list[AuthUserSchema])
async def get_users(
        session: Annotated[
            AsyncSession,
            Depends(db_helper.session_getter),
        ],
):
    users = await get_all_users(session=session)
    return users


# Вспомогательная функция для basic_auth_username
async def get_auth_user_username(
        session: Annotated[
                    AsyncSession,
                    Depends(db_helper.session_getter),
                ],
        credentials: Annotated[HTTPBasicCredentials, Depends(security)],
) -> TokenResponseSchema:
    username = credentials.username

    unauthed_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid username or password",
        headers={"WWW-Authenticate": "Basic"},
    )

    # Проверка попыток входа через redis
    key = f"failed_attempts:{username}"
    attempts = await redis_client.get(key)
    attempts = int(attempts) if attempts else 0

    if attempts >= MAX_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Too many failed attempts, try again later"
        )

    # Запрос пользователя из user_service
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{settings.user_service_url}/api/v1/users/username/{username}/")

    if response.status_code != 200:
        logger.error(f"Ошибка при авторизации: пользователь не найден в user_service")
        await redis_client.incr(key)
        await redis_client.expire(key, BLOCK_TIME_SECONDS)
        raise unauthed_exc

    user_data = response.json()
    user_id = user_data.get("user_id")
    username = user_data.get("username")
    user_email = user_data.get("email")
    is_active = user_data.get("is_active")

    if not user_id or not is_active:
        logger.error(f"Ошибка при авторизации: user_id = \"{user_id}\", is_active = \"{is_active}\"")
        await redis_client.incr(key)
        await redis_client.expire(key, BLOCK_TIME_SECONDS)
        raise unauthed_exc

    # Запрос пользователя из auth_service
    auth_user: AuthUserModel = await get_auth_user(user_id, session)

    if not auth_user:
        logger.error(f"Ошибка при авторизации: пользователь не найден в auth_service")
        await redis_client.incr(key)
        await redis_client.expire(key, BLOCK_TIME_SECONDS)
        raise unauthed_exc

    # secrets
    if not verify_password(credentials.password, auth_user.password):
        logger.error(f"Ошибка при авторизации: пароли не совпадают")
        await redis_client.incr(key)
        await redis_client.expire(key, BLOCK_TIME_SECONDS)
        raise unauthed_exc

    await redis_client.delete(key)

    # Генерируем новые токены
    refresh_token = create_refresh_token(user_id, user_email)
    access_token = create_access_token(user_id, user_email)

    # Инвалидируем старый токен и прикрепляем новый
    await update_refresh_token(session, auth_user, refresh_token)

    return TokenResponseSchema(
        user_id=user_id,
        username=username,
        email=user_email,
        access_token=access_token,
        refresh_token=refresh_token,
    )


# Авторизируем пользователя через username\password
@router.post("/login/")
def basic_auth_username(
        token_data: TokenResponseSchema = Depends(get_auth_user_username)
):
    # Выдаем access_token и refresh_token
    logger.info(f"Auth via user/password - successfully")
    return token_data


@router.get("/check-token-auth/")
async def check_token_auth(
        credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
):
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
            headers={"WWW-Authenticate": "Bearer"}
        )
    token = credentials.credentials
    try:
        username = await get_username_by_static_auth_token(token)
    except Exception as e:
        raise e
    return {
        "message": f"Hi!, {username}!",
        "username": username,
    }


@router.delete("/{user_id}")
async def delete_auth_user_account(
        user_id: int,
        session: Annotated[
                    AsyncSession,
                    Depends(db_helper.session_getter),
                ],
):
    """
    Используется через user_service, \n
    Не синхронизует данные через эту сторону
    """
    # 1 Есть ли пользователь в auth_service
    auth_user = await get_auth_user(user_id, session)
    if not auth_user:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail=f"User with {user_id} not found in auth_service"
        )

    await delete_auth_user(user_id, session)

    return {"message": "Auth user deleted"}
