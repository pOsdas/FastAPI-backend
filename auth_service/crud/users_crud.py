"""
create
read
update
delete
"""
import httpx
import json
from typing import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth_service.core.config import settings
from auth_service.core.models import AuthUser as AuthUserModel
from auth_service.core.schemas import AuthUser as AuthUserSchema
from auth_service.core.redis_client import redis_client


async def get_all_users(
        session: AsyncSession
) -> Sequence[AuthUserModel]:
    stmt = select(AuthUserModel).order_by(AuthUserModel.user_id)
    result = await session.scalars(stmt)
    return result.all()


async def get_auth_user(
        user_id: int,
        session: AsyncSession
) -> AuthUserSchema:
    stmt = select(AuthUserModel).where(AuthUserModel.user_id == user_id)
    result = await session.execute(stmt)
    auth_user = result.scalar_one_or_none()
    return auth_user


# --- with request to user_service ---

async def get_user_service_user_by_id(user_id: int):
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            f"{settings.user_service_url}/api/v1/users/{user_id}/"
        )
        response.raise_for_status()

    return response.json()


async def get_user_service_user_by_username(username: str):
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            f"{settings.user_service_url}/api/v1/users/username/{username}/"
        )
        response.raise_for_status()

    return response.json()


async def create_user_service_user(username, email):
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            f"{settings.user_service_url}/api/v1/users/create_user/",
            json={
                "username": username,
                "email": email,
            }
        )
        response.raise_for_status()

    return response.json()

# ------------------------------------


async def delete_auth_user_redis_data(user) -> None:
    user_id = user.user_id
    user_data = await get_user_service_user_by_id(user_id)
    username = user_data.get("username")

    # Удаляем счетчик неудачных попыток
    await redis_client.delete(f"failed_attempts:{username}")


async def delete_auth_user(
        user_id: int,
        session: AsyncSession
):
    stmt = select(AuthUserModel).where(AuthUserModel.user_id == user_id)
    result = await session.execute(stmt)
    auth_user = result.scalar_one_or_none()

    # Удаляем redis
    try:
        await delete_auth_user_redis_data(auth_user)
    except Exception as e:
        print(f"Failed to delete redis data: {str(e)}")

    # Сохраняем
    await session.delete(auth_user)
    try:
        await session.commit()
    except Exception as e:
        await session.rollback()
        print(f"Failed to delete user: {str(e)}")

