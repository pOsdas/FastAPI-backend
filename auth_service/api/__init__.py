from fastapi import APIRouter

from auth_service.core.config import settings
from .api_v1 import api_v1_router

router = APIRouter(
    prefix=settings.api.prefix,
)
router.include_router(api_v1_router)
