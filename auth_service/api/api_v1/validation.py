from typing import Annotated
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jwt import exceptions
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from sqlalchemy.future import select

from auth_service.core.models import db_helper
from .utils.helpers import TOKEN_TYPE_FIELD, ACCESS_TOKEN_TYPE, REFRESH_TOKEN_TYPE
from auth_service.core import security
from auth_service.core.models import AuthUser as AuthUserModel

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="api/v1/auth/jwt/login/",
)


def get_current_token_payload(
    # credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
    token: str = Depends(oauth2_scheme)
) -> dict:
    # token = credentials.credentials
    try:
        payload = security.decode_jwt(
            token=token
        )
    except exceptions.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token error"
        )
    return payload


def validate_token_type(
        payload: dict,
        token_type: str
) -> bool:
    current_token_type = payload.get(TOKEN_TYPE_FIELD)
    if current_token_type == token_type:
        return True
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=f"Invalid token type {current_token_type!r} expected {token_type!r}",
    )


async def get_user_by_token_sub(
        payload: dict,
        session: Annotated[
                AsyncSession,
                Depends(db_helper.session_getter)
            ]
) -> AuthUserModel:
    user_id: int | None = payload.get("sub")
    stmt = select(AuthUserModel).where(AuthUserModel.user_id == user_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if user:
        return user

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token invalid or expired"
    )


def get_auth_user_from_token_of_type(token_type: str):
    async def get_auth_user_from_token(
            session: Annotated[
                AsyncSession,
                Depends(db_helper.session_getter)
            ],
            payload: dict = Depends(get_current_token_payload),
    ):
        validate_token_type(payload=payload, token_type=token_type)
        return await get_user_by_token_sub(payload, session)
    return get_auth_user_from_token


get_current_auth_user = get_auth_user_from_token_of_type(ACCESS_TOKEN_TYPE)
get_current_auth_user_for_refresh = get_auth_user_from_token_of_type(REFRESH_TOKEN_TYPE)