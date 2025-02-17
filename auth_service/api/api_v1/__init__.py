from fastapi import APIRouter

from auth_service.core.config import settings

from .auth import router as auth_router
from .jwt_auth import router as jwt_router

api_v1_router = APIRouter(
    prefix=settings.api.v1.prefix,
)

api_v1_router.include_router(
    auth_router,
    # prefix=settings.api.v1.auth,
)

api_v1_router.include_router(
    jwt_router,
    # prefix=settings.api.v1.jwt,
)





