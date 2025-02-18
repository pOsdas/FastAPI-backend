import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI

from core.config import settings
from user_service.api import router as users_router
from core.models.db_helper import db_helper


@asynccontextmanager
async def lifespan(users_app: FastAPI):
    # startup
    yield
    # shutdown
    await db_helper.dispose()


users_app = FastAPI(
    lifespan=lifespan
)
users_app.include_router(router=users_router)


@users_app.get("/")
def hello_index():
    return {
        "message": "Hello"
    }


@users_app.get("/user_service")
def hello_index():
    return {
        "message": "Hello from User-Service"
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:users_app",
        # host=settings.run.host,
        # port=settings.run.port,
        reload=True,
    )
