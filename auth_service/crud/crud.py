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
from auth_service.core.security import hash_password
# from auth_service.core.schemas import AuthUser

# ### fake users db
john = AuthUserModel(
    user_id=1,
    password=hash_password("qwerty"),
    # updated_at
    refresh_token="dummy_refresh_token"
)

sam = AuthUserModel(
    user_id=2,
    password=hash_password("secret"),
    # updated_at
    refresh_token="second_dummy_refresh_token"
)


test = AuthUserModel(
    user_id=3,
    password=hash_password("test"),
    # updated_at
    refresh_token="second_dummy_refresh_token"
)

users_db: dict[int, AuthUserModel] = {
    john.user_id: john,
    sam.user_id: sam,
}
user_id_to_password = {"3": "test"}
static_auth_token_to_user_id = {
    "90609ed991fcca984411d4b6e1ba7": john.user_id,
}
# ### never do like that


async def get_all_users(
        session: AsyncSession
) -> Sequence[AuthUserModel]:
    stmt = select(AuthUserModel).order_by(AuthUserModel.user_id)
    result = await session.scalars(stmt)
    return result.all()
