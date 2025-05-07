"""
create
read
update
delete
"""
from typing import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth_service.core.models import AuthUser as AuthUserModel
from auth_service.core.schemas import AuthUser as AuthUserSchema
from auth_service.core.security import hash_password
# from auth_service.core.schemas import AuthUser


async def get_all_users(
        session: AsyncSession
) -> Sequence[AuthUserModel]:
    stmt = select(AuthUserModel).order_by(AuthUserModel.user_id)
    result = await session.scalars(stmt)
    return result.all()


async def get_auth_user(
        user_id: int,
        session: AsyncSession
) -> AuthUserSchema:
    stmt = select(AuthUserModel).where(AuthUserModel.user_id == user_id)
    result = await session.execute(stmt)
    auth_user = result.scalar_one_or_none()
    return auth_user


async def delete_auth_user(
        user_id: int,
        session: AsyncSession
):
    stmt = select(AuthUserModel).where(AuthUserModel.user_id == user_id)
    result = await session.execute(stmt)
    auth_user = result.scalar_one_or_none()

    await session.delete(auth_user)
    try:
        await session.commit()
    except Exception as e:
        await session.rollback()
        print(f"Failed to delete user: {str(e)}")

