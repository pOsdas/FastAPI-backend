from typing import Annotated
import redis.asyncio as redis
import httpx
from fastapi import (
    APIRouter, Depends, HTTPException,
    status, Header,
)
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth_service.core.models import db_helper
from auth_service.core.models.auth_user import AuthUser as AuthUserModel
from auth_service.core.config import settings
from auth_service.core.security import verify_password, hash_password
from auth_service.core.schemas import RegisterUserSchema
from auth_service.core.schemas import AuthUser as AuthUserSchema
from auth_service.crud.crud import (
    static_auth_token_to_user_id,
    get_all_users, delete_auth_user, get_auth_user
)

router = APIRouter(prefix="/auth", tags=["AUTH"])

security = HTTPBasic()

# Подключение к Redis
redis_client = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

# failed attempts
MAX_ATTEMPTS = 5
BLOCK_TIME_SECONDS = 300  # 5 минут


@router.get("/basic-auth/")
def demo_basic_auth_credentials(
        credentials: Annotated[HTTPBasicCredentials, Depends(security)],
):
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
):
    # 1 Запрос на создание
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.user_service_url}/api/v1/users/create_user",
            json={
                "username": user_data.username,
                "email": user_data.email,
            }
        )

    if response.status_code not in (200, 201):
        print(f"response.status_code: {response.status_code}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user profile in user_service",
        )

    user_profile = response.json()
    user_id = user_profile.get("id")
    if not user_id:
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

    return {"message": "User registered successfully", "user_id": user_id}


@router.get("/get_users", response_model=list[AuthUserSchema])
async def get_users(
        session: Annotated[
            AsyncSession,
            Depends(db_helper.session_getter),
        ],
):
    users = await get_all_users(session=session)
    return users


async def get_auth_user_username(
        session: Annotated[
                    AsyncSession,
                    Depends(db_helper.session_getter),
                ],
        credentials: Annotated[HTTPBasicCredentials, Depends(security)],
) -> str:
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
        response = await client.get(f"{settings.user_service_url}/api/v1/users/username/{username}")

    if response.status_code != 200:
        await redis_client.incr(key)
        await redis_client.expire(key, BLOCK_TIME_SECONDS)
        raise unauthed_exc  # Пользователь не найден

    user_data = response.json()
    user_id = user_data.get("id")
    is_active = user_data.get("is_active")

    if not user_id or not is_active:
        await redis_client.incr(key)
        await redis_client.expire(key, BLOCK_TIME_SECONDS)
        raise unauthed_exc

    stmt = select(AuthUserModel.password).where(AuthUserModel.user_id == user_id)
    result = await session.execute(stmt)
    auth_user = result.scalar_one_or_none()

    if not auth_user:
        await redis_client.incr(key)
        await redis_client.expire(key, BLOCK_TIME_SECONDS)
        raise unauthed_exc

    hashed_password = auth_user

    # secrets
    if not verify_password(credentials.password, hashed_password):
        await redis_client.incr(key)
        await redis_client.expire(key, BLOCK_TIME_SECONDS)
        raise unauthed_exc

    await redis_client.delete(key)

    return username


def get_username_by_static_auth_token(
        static_token: str = Header(alias="x-auth-token")
) -> str:
    if username := static_auth_token_to_user_id.get(static_token):
        return username
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid token"
    )


@router.get("/basic-auth-username/")
def demo_basic_auth_username(
        auth_username: str = Depends(get_auth_user_username)
):
    return {
        "message": f"Hi!, {auth_username}!",
        "username": auth_username,
    }


@router.get("/check-token-auth/")
def check_token_auth(
        username: str = Depends(get_username_by_static_auth_token)
):
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
    Используется через user_service
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
