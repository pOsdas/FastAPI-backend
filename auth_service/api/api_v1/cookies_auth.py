import uuid
import json
from time import time
from typing import Any
from fastapi import (
    APIRouter, Depends, HTTPException,
    status, Response, Cookie,
    Request,
)

from auth_service.core.redis_client import redis_client
from auth_service.core.config import settings
from auth_service.crud.tokens_crud import get_username_by_static_auth_token
from auth_service.core.logger import logger

router = APIRouter(prefix="/cookies", tags=["COOKIES"])


def generate_session_id() -> str:
    return uuid.uuid4().hex


async def get_session_data(
        session_id: str = Cookie(alias=settings.cookie_session_id_key)
) -> dict[str, Any]:
    data = await redis_client.get(f"{settings.session_prefix}{session_id}")
    if not data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="not authenticated"
        )

    return json.loads(data)


# Авторизируем пользователя через cookies
@router.post("/login-cookie/")
async def login_cookie(
        response: Response,
        username: str = Depends(get_username_by_static_auth_token)
) -> dict[str, Any]:
    session_id = generate_session_id()
    session_data = {
        "username": username,
        "login_at": int(time()),
    }
    # TTL на ключ
    await redis_client.setex(
        f"{settings.session_prefix}{session_id}",
        settings.session_ttl_seconds,
        json.dumps(session_data)
    )
    response.set_cookie(
        key=settings.cookie_session_id_key,
        value=session_id,
        httponly=settings.httponly,  # javascript protection
        secure=settings.secure,  # https (set "True" in real projects)
        samesite=settings.same_site,  # CSRF protection
        domain=settings.domain,
        max_age=settings.session_ttl_seconds,
    )

    logger.info(f"Cookie created successfully: {session_id}")
    return {"result": "ok"}


@router.get("/get_session_id")
async def get_cookie_session_id(request: Request):
    """
    Вручную получить cookie_session_id (для тестирования в Swagger)
    """
    session_cookie = request.cookies.get(settings.cookie_session_id_key)
    if not session_cookie:
        return {"error": "Сессионный cookie не найден."}
    return {"session_id": session_cookie}


@router.get("/check-cookie/")
def check_cookie(
        user_session_data: dict = Depends(get_session_data),
):
    return {
        "message": f"Hello, {user_session_data['username']}",
        **user_session_data,
    }


@router.get("/logout-cookie/")
async def cookie_logout(
        response: Response,
        session_id: str = Cookie(alias=settings.cookie_session_id_key),
):
    await redis_client.delete(f"session:{session_id}")
    response.delete_cookie(settings.cookie_session_id_key)

    logger.info(f"Cookie deleted successfully: {session_id}")
    return {"result": "bye"}
