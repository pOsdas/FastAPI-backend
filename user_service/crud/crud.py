"""
create
read
update
delete
"""
from typing import Sequence
from fastapi import HTTPException, status

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from user_service.core.models import User
from user_service.core.schemas.user import CreateUser


async def get_all_users(
        session: AsyncSession
) -> Sequence[User]:
    stmt = select(User).order_by(User.user_id)
    result = await session.scalars(stmt)
    return result.all()


async def get_user(
        session: AsyncSession,
        user_id: int
) -> User | None:
    return await session.get(User, user_id)


async def get_user_by_email(
        session: AsyncSession,
        email: str,
) -> User | None:
    result = await session.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def create_user(
        session: AsyncSession,
        user_create: CreateUser,
) -> User:
    user = User(**user_create.model_dump())
    session.add(user)
    await session.commit()
    return user


async def delete_user(
        user_id: int,
        session: AsyncSession,
):
    stmt = select(User).where(User.user_id == user_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    await session.delete(user)
    try:
        await session.commit()
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user: {str(e)}"
        )

    return {"message": "User deleted successfully", "id": user_id}
