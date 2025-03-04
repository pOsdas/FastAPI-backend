from datetime import timedelta

from auth_service.core import security as auth_utils
from auth_service.core.config import settings
from auth_service.core.schemas import AuthUser as AuthUserSchema, CombinedUserSchema


TOKEN_TYPE_FIELD = "type"
ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"


def create_jwt(
        token_type: str,
        token_data: dict,
        expires_in: int = settings.auth_jwt.access_token_expires_in,
        expire_timedelta: timedelta | None = None,
) -> str:
    jwt_payload = {TOKEN_TYPE_FIELD: token_type}
    jwt_payload.update(token_data)
    return auth_utils.encode_jwt(
        payload=jwt_payload,
        expires_in=expires_in,
        expire_timedelta=expire_timedelta,
    )


def create_access_token(user: CombinedUserSchema) -> str:
    jwt_payload = {
        # subject
        "sub": user.user_id,
        "user_id": user.user_id,
        "email": user.email,
    }

    return create_jwt(
        token_type=ACCESS_TOKEN_TYPE,
        token_data=jwt_payload,
        expires_in=settings.auth_jwt.access_token_expires_in,
    )


def create_refresh_token(user: CombinedUserSchema) -> str:
    jwt_payload = {
        "sub": user.user_id,
        "user_id": user.email,
    }
    return create_jwt(
        token_type=REFRESH_TOKEN_TYPE,
        token_data=jwt_payload,
        expire_timedelta=timedelta(days=settings.auth_jwt.refresh_token_expires_days),
    )
