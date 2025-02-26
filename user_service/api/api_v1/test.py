from fastapi import (
    APIRouter,
    HTTPException,
)

from user_service.core.schemas.user import UserSchema, UserUpdateSchema
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
