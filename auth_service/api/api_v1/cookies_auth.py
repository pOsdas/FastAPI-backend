import uuid
from time import time
from typing import Any
from fastapi import (
    APIRouter, Depends, HTTPException,
    status, Response, Cookie,
    Request,
)

# will be deleted in the future
from .auth import get_username_by_static_auth_token

router = APIRouter(prefix="/cookies", tags=["COOKIES"])

# ### for test only never do like this

COOKIES: dict[str, dict[str, Any]] = {}
COOKIE_SESSION_ID_KEY = "cookie_session_id"

# ###


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