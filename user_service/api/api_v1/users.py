from typing import Annotated
from datetime import datetime

from fastapi import (
    APIRouter,
    HTTPException,
    Depends,
    BackgroundTasks,
    Body,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from user_service.api.api_v1.utils.send_welcome_email import send_welcome_email
from user_service.core.models import db_helper
from user_service.core.schemas.user import CreateUser, ReadUser, UserSchema, UserUpdateSchema
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
    2: {
        "id": 2,
        "username": "thomas",
        "email": "thomas@example.com",
        "is_active": False,
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
        # background_tasks: BackgroundTasks,

):
    exiting_user = await crud.get_user_by_email(
        session,
        user_create.email
    )
    if exiting_user:
        raise HTTPException(
            status_code=409, detail="User with such email already exists"
        )

    else:
        user = await crud.create_user(
            session=session,
            user_create=user_create,
        )
        # background_tasks.add_task(send_welcome_email, user_id=user.id)
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


@router.patch("/change_user/{user_id}", response_model=UserSchema)
async def update_user(
        user_id: int,
        data: Annotated[
            UserUpdateSchema,
            Body()
        ],
        session: Annotated[
            AsyncSession,
            Depends(db_helper.session_getter),
        ],
):
    user = await crud.get_user(session=session, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    updated = False

    if data.new_name:
        user.username = data.new_name
        updated = True
    if data.email:
        user.email = data.email
        updated = True
    if data.is_active:
        user.is_active = data.is_active
        updated = True

    if not updated:
        raise HTTPException(status_code=400, detail="No data provided for update")

    try:
        session.add(user)
        await session.commit()
        await session.refresh(user)
    except SQLAlchemyError as e:
        await session.rollback()
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    return user


@router.patch("/test_change_user/{user_id}", response_model=UserSchema)
async def test_update_user(
        user_id: int,
        data: UserUpdateSchema,
):
    """
    Тестовая функция без подключения к базе данных
    """
    user = fake_users_db.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if data.new_name:
        user["username"] = data.new_name
    if data.email:
        user["email"] = data.email

    return user






