import secrets
import uuid
from typing import Annotated, Any
from time import time

import httpx
from fastapi import (
    APIRouter, Depends, HTTPException,
    status, Header, Response, Cookie,
    Request,
)
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth_service.core.models import db_helper
from auth_service.core.models.auth_user import AuthUser as AuthUserModel
from auth_service.core.config import settings
from auth_service.core.security import verify_password, hash_password
from auth_service.core.schemas import RegisterUserSchema
from auth_service.crud.crud import user_id_to_password, static_auth_token_to_user_id

router = APIRouter(prefix="/auth", tags=["AUTH"])

security = HTTPBasic()

# ### for test only never do like this

COOKIES: dict[str, dict[str, Any]] = {}
COOKIE_SESSION_ID_KEY = "cookie_session_id"
failed_attempts = {}

# ###


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


async def get_auth_user_username(
        session: Annotated[
                    AsyncSession,
                    Depends(db_helper.session_getter),
                ],
        credentials: Annotated[HTTPBasicCredentials, Depends(security)],
) -> str:
    unauthed_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid username or password",
        headers={"WWW-Authenticate": "Basic"},
    )
    if failed_attempts.get(credentials.username, 0) >= 3:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Too many failed attempts"
        )

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{settings.user_service_url}/api/v1/users/username/{credentials.username}")

    if response.status_code != 200:
        raise unauthed_exc  # Пользователь не найден

    user_data = response.json()
    user_id = user_data.get("id")
    is_active = user_data.get("is_active")

    if not user_id or not is_active:
        raise unauthed_exc

    stmt = select(AuthUserModel.password).where(AuthUserModel.user_id == user_id)
    result = await session.execute(stmt)
    auth_user = result.scalar_one_or_none()

    if not auth_user:
        raise unauthed_exc

    hashed_password = auth_user

    # secrets
    if not verify_password(credentials.password, hashed_password):
        failed_attempts[credentials.username] = failed_attempts.get(credentials.username, 0) + 1
        raise unauthed_exc

    if credentials.username in failed_attempts:
        del failed_attempts[credentials.username]

    return credentials.username


def get_username_by_static_auth_token(
        static_token: str = Header(alias="x-auth-token")
) -> str:
    if username := static_auth_token_to_user_id.get(static_token):
        return username
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid token"
    )


def generate_session_id() -> str:
    return uuid.uuid4().hex


def get_session_data(
        session_id: str = Cookie(alias=COOKIE_SESSION_ID_KEY)
) -> dict:
    if session_id not in COOKIES:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="not authenticated"
        )

    return COOKIES[session_id]


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


@router.post("/login-cookie/")
def demo_auth_login_cookie(
        response: Response,
        username: str = Depends(get_username_by_static_auth_token)
) -> dict:
    session_id = generate_session_id()
    COOKIES[session_id] = {
        "username": username,
        "login_at": int(time()),
    }
    response.set_cookie(
        key=COOKIE_SESSION_ID_KEY,
        value=session_id,
        httponly=True,  # javascript protection
        secure=False,  # https (set "True" in real projects)
        samesite="lax",  # CSRF protection
        domain="127.0.0.1",
    )
    return {"result": "ok"}


@router.get("/get_session_id")
async def get_cookie_session_id(request: Request):
    """
    Вручную получить cookie_session_id (для тестирования в Swagger)
    """
    session_cookie = request.cookies.get("cookie_session_id")
    # session_cookie = request.cookies.get("session")
    if not session_cookie:
        return {"error": "Сессионный cookie не найден."}
    return {"session_id": session_cookie}


@router.get("/check-cookie/")
def demo_auth_check_cookie(
        user_session_data: dict = Depends(get_session_data),
):
    username = user_session_data["username"]
    return {
        "message": f"Hello, {username}",
        **user_session_data,
    }


@router.get("/logout-cookie/")
def demo_auth_cookie_logout(
        response: Response,
        session_id: str = Cookie(alias=COOKIE_SESSION_ID_KEY),
        user_session_data: dict = Depends(get_session_data)
):
    COOKIES.pop(session_id)
    response.delete_cookie(COOKIE_SESSION_ID_KEY)
    username = user_session_data["username"]
    return {
        "message": f"Bye, {username}",
    }