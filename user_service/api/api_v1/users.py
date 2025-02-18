from typing import Annotated
from datetime import datetime

from fastapi import (
    APIRouter,
    HTTPException,
    Depends,
    BackgroundTasks,
)
from sqlalchemy.ext.asyncio import AsyncSession

from user_service.api.api_v1.utils.send_welcome_email import send_welcome_email
from user_service.core.models import db_helper
from user_service.core.schemas.user import CreateUser, ReadUser, UserSchema
from user_service.crud import crud

router = APIRouter(
    prefix="/users", tags=["Users"],
)


fake_users_db = {
    1: {
        "id": 1,
        "username": "john_doe",
        "email": "john@example.com",
        "is_active": True,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    },
    # Можно добавить и других пользователей
}


@router.post("/create_user", response_model=ReadUser)
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


@router.get("/get_users", response_model=list[ReadUser])
async def get_users(
        session: Annotated[
            AsyncSession,
            Depends(db_helper.session_getter),
        ],
):
    users = await crud.get_all_users(session=session)
    return users


@router.get("/{user_id}", response_model=UserSchema)
async def get_user(user_id: int):
    user = fake_users_db.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user




