import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI

from core.config import settings
from auth_service.api.api_v1.auth import router as auth_router
from core.models.db_helper import db_helper


@asynccontextmanager
async def lifespan(auth_app: FastAPI):
    # startup
    yield
    # shutdown
    await db_helper.dispose()


auth_app = FastAPI(
    lifespan=lifespan
)
auth_app.include_router(router=auth_router, prefix=settings.api.prefix)


@auth_app.get("/auth_service")
def hello_index():
    return {
        "message": "Hello from Auth-Service"
    }


if __name__ == "__main__":
    uvicorn.run("main:auth_app", reload=True)
