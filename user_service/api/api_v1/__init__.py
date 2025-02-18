from fastapi import APIRouter

from user_service.core.config import settings

from .users import router as users_router

api_v1_router = APIRouter(
    prefix=settings.api.v1.prefix,
)
api_v1_router.include_router(
    users_router,
    # prefix=settings.api.v1.users,
)
