import httpx
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from auth_service.core.models import AuthUser as AuthUserModel
from auth_service.core.security import decode_jwt
from auth_service.core.config import settings


# ---- tokens ----
def get_user_id_by_static_auth_token(
        token: str
) -> int | None:
    try:
        payload = decode_jwt(token)
    except Exception as e:
        raise

    user_id = payload.get("sub")
    return int(user_id) if user_id else None


async def get_username_by_static_auth_token(token) -> str:
    user_id = get_user_id_by_static_auth_token(token)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    # Запрос к user_service
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.user_service_url}/api/v1/users/{user_id}/"
            )
            response.raise_for_status()

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="User service error"
        )

    except httpx.RequestError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cannot reach user service"
        )

    data = response.json()
    username = data.get("username")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Malformed user data"
        )
    return username


async def update_refresh_token(
    session: AsyncSession,
    user: AuthUserModel,
    new_token: str
):
    user.refresh_token = new_token
    session.add(user)
    try:
        await session.commit()
    except Exception:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update refresh token"
        )
