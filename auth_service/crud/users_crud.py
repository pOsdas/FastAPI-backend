"""
create
read
update
delete
"""
import httpx
from typing import Sequence
from sqlalchemy import select
from functools import wraps
from typing import Callable, Coroutine, Any
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from auth_service.core.logger import logger
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

def handle_user_service_errors(
        detail_prefix: str = "",
        success_status: int = 200
):
    def decorator(func: Callable[..., Coroutine[Any, Any, httpx.Response]]):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                response = await func(*args, **kwargs)
                if response.status_code != success_status:
                    response.raise_for_status()
                return response

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"{detail_prefix}Not found"
                    )
                elif e.response.status_code == 400:
                    error_detail = e.response.json().get("detail", "Bad request")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"{detail_prefix}{error_detail}"
                    )
                else:
                    logger.error(f"User service error: {e.response.status_code}")
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail=f"{detail_prefix}External service error"
                    )

            except httpx.RequestError as e:
                logger.error(f"Connection error: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"{detail_prefix}Service unavailable"
                )

            except Exception as e:
                logger.critical(f"Unexpected error: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"{detail_prefix}Internal error"
                )

        return wrapper

    return decorator


@handle_user_service_errors(detail_prefix="By ID: ")
async def get_user_service_user_by_id(user_id: int):
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            f"{settings.user_service_url}/api/v1/users/{user_id}/"
        )
        response.raise_for_status()

    return response


@handle_user_service_errors(detail_prefix="By username: ")
async def get_user_service_user_by_username(username: str):
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            f"{settings.user_service_url}/api/v1/users/username/{username}/"
        )
        response.raise_for_status()

    return response


@handle_user_service_errors(detail_prefix="User creation: ", success_status=201)
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

    return response

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

