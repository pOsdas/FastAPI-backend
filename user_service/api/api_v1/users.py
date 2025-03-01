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
from sqlalchemy.future import select

from user_service.api.api_v1.utils.send_welcome_email import send_welcome_email
from user_service.core.models import db_helper, User
from user_service.core.schemas.user import CreateUser, ReadUser, UserSchema, UserUpdateSchema
from user_service.crud import crud
from .utils.fake_db import fake_users_db

router = APIRouter(
    prefix="/users", tags=["Users"],
)


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


@router.get("/username/{username}", response_model=UserSchema)
async def get_user_by_username(
        username: str,
        session: Annotated[
            AsyncSession,
            Depends(db_helper.session_getter),
        ],
):
    result = await session.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()

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


@router.delete("{user_id}")
async def delete_user(
        user_id: int,
        session: Annotated[
            AsyncSession,
            Depends(db_helper.session_getter),
        ],

):
    user = await crud.get_user(session=session, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        await session.delete(user)
        await session.commit()
    except SQLAlchemyError as e:
        await session.rollback()
        print(f"Database error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error")

    return user
