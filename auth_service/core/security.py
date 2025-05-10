import jwt
from jwt import (
    ExpiredSignatureError,
    InvalidSignatureError,
    InvalidTokenError,
    PyJWTError,
)
import bcrypt
from datetime import datetime, timezone, timedelta

from fastapi import HTTPException, status
from passlib.context import CryptContext

from .config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def encode_jwt(
        payload: dict,
        private_key: str = settings.auth_jwt.private_key_path.read_text(),
        algorithm: str = settings.auth_jwt.algorithm,
        expires_in: int = settings.auth_jwt.access_token_expires_in,  # minutes
        expire_timedelta: timedelta | None = None,
):
    to_encode = payload.copy()
    now = datetime.now(timezone.utc)
    if expire_timedelta:
        expire = now + expire_timedelta
    else:
        expire = now + timedelta(minutes=expires_in)
    to_encode.update(
        exp=expire,
        iat=now,
    )
    encoded = (
        jwt.encode(
            to_encode,
            private_key,
            algorithm=algorithm)
    )
    return encoded


def decode_jwt(
        token: str | bytes,
        public_key: str = settings.auth_jwt.public_key_path.read_text(),
        algorithm: str = settings.auth_jwt.algorithm,
):
    try:
        decoded = jwt.decode(
            token,
            public_key,
            algorithms=[algorithm],
            options={"verify_exp": True},
        )
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
        )

    except (InvalidSignatureError, InvalidTokenError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
        )
    except PyJWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token validation failed: {str(e)}",
        )

    return decoded


def hash_password(password: str) -> bytes:
    salt = bcrypt.gensalt()
    pwd_bytes: bytes = password.encode()
    return bcrypt.hashpw(pwd_bytes, salt)


def validate_password(
        password: str,
        hashed_password: bytes
) -> bool:
    return bcrypt.checkpw(
        password.encode(),
        hashed_password=hashed_password,
    )


def verify_password(
        plain_password: str,
        hashed_password: str,
) -> bool:
    return pwd_context.verify(plain_password, hashed_password)