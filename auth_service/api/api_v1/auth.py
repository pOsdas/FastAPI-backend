# auth.py

import secrets
import uuid
from typing import Annotated, Any
from time import time

from fastapi import (
    APIRouter, Depends, HTTPException,
    status, Header, Response, Cookie,
)
from fastapi.security import HTTPBasic, HTTPBasicCredentials

router = APIRouter(prefix="/auth", tags=["auth"])

security = HTTPBasic()

usernames_to_password = {"demo_user": "demo_password"}  # на самом деле здесь должны быть хешированные пароли
static_auth_token_to_username = {"static-token": "demo_user"}
COOKIE_SESSION_ID_KEY = "session_id"
COOKIES = {}


@router.get("/basic-auth/")
def demo_basic_auth_credentials(
        credentials: Annotated[HTTPBasicCredentials, Depends(security)],
):
    return {
        "message": "Hi!",
        "username": credentials.username,
        "password": credentials.password,
    }


def get_auth_user_username(
        credentials: Annotated[HTTPBasicCredentials, Depends(security)],
) -> str:
    unauthed_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid username or password",
        headers={"WWW-Authenticate": "Basic"},
    )
    correct_password = usernames_to_password.get(credentials.username)
    if correct_password is None:
        raise unauthed_exc

    # secrets
    if not secrets.compare_digest(
        credentials.password.encode("utf-8"),
        correct_password.encode("utf-8",)
    ):
        raise unauthed_exc

    return credentials.username


def get_username_by_static_auth_token(
        static_token: str = Header(alias="x-auth-token")
) -> str:
    if username := static_auth_token_to_username.get(static_token):
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


@router.get("/some-http-header-auth/")
def demo_auth_some_http_header(
        username: str = Depends(get_username_by_static_auth_token)
):
    return {
        "message": f"Hi!, {username}!",
        "username": username,
    }


@router.post("/login-cookie/")
def demo_auth_login_cookie(
        response: Response,
        # auth_username: str = Depends(get_auth_user_username)
        username: str = Depends(get_username_by_static_auth_token)
):
    session_id = generate_session_id()
    COOKIES[session_id] = {
        "username": username,
        "login_at": int(time()),
    }
    response.set_cookie(COOKIE_SESSION_ID_KEY, session_id)
    return {"result": "ok"}


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