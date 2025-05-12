from fastapi import (
    APIRouter, Request, Depends,
)
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from auth_service.core.models import db_helper
from auth_service.core.schemas import RevokeTokenResponseSchema
from auth_service.crud.tokens_crud import print_all_revoked_tokens

router = APIRouter(prefix="/test", tags=["TEST"])


@router.get("/set_session")
async def set_session(request: Request):
    """
    Тестирование cookies
    """
    request.session["test_key"] = "test_value"
    return {"message": "Session set"}


@router.get("/get_session")
async def get_session(request: Request):
    """
    Тестирование cookies
    """
    value = request.session.get("test_key", "not found")
    return {"session_value": value}


@router.get("/get_revoked_tokens/", response_model=list[RevokeTokenResponseSchema])
async def get_revoked_tokens(
        session: Annotated[
            AsyncSession,
            Depends(db_helper.session_getter),
        ],
):
    tokens = await print_all_revoked_tokens(session=session)
    return tokens
