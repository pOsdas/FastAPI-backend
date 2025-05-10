from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from auth_service.crud.users_crud import get_user_service_user_by_id
from auth_service.core.models import AuthUser as AuthUserModel
from auth_service.core.security import decode_jwt


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
        response = await get_user_service_user_by_id(user_id=user_id)
    except Exception as e:
        raise e

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
