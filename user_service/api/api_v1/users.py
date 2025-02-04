from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    BackgroundTasks,
)
from sqlalchemy.ext.asyncio import AsyncSession

from user_service.api.api_v1.utils.send_welcome_email import send_welcome_email
from user_service.core.models import db_helper
from user_service.core.schemas.user import CreateUser, ReadUser
from user_service.crud import crud

router = APIRouter(
    tags=["Users"],
)


@router.get("", response_model=list[ReadUser])
async def get_users(
        session: Annotated[
            AsyncSession,
            Depends(db_helper.session_getter),
        ],
):
    users = await crud.get_all_users(session=session)
    return users


@router.post("", response_model=ReadUser)
async def create_user(
        session: Annotated[
            AsyncSession,
            Depends(db_helper.session_getter),
        ],
        user_create: CreateUser,
        background_tasks: BackgroundTasks,

):
    user = await crud.create_user(
        session=session,
        user_create=user_create,
    )
    background_tasks.add_task(send_welcome_email, user_id=user.id)
    return user

