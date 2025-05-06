from typing import Annotated
from fastapi import (
    APIRouter,
    HTTPException,
    Depends,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from user_service.crud import crud
from user_service.core.schemas.user import UserSchema, UserUpdateSchema
from user_service.core.models import db_helper
from .utils.fake_db import fake_users_db


router = APIRouter(
    prefix="/test", tags=["TEST"],
)


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


@router.delete("/{user_id}")
async def test_delete_user_service_user(
        user_id: int,
        session: Annotated[
            AsyncSession,
            Depends(db_helper.session_getter),
        ],

):
    """
    Удаляет пользователя только на этой стороне!
    """
    user = await crud.get_user(session=session, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Пользователь найден
    await crud.delete_user(user.user_id, session)

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
