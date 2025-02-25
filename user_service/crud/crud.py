"""
create
read
update
delete
"""
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from user_service.core.models import User
from user_service.core.schemas.user import CreateUser


async def get_all_users(
        session: AsyncSession
) -> Sequence[User]:
    stmt = select(User).order_by(User.id)
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
