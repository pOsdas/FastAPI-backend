import asyncio
from concurrent.futures import ThreadPoolExecutor

import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI

from core.config import settings
from core.models import Base
from user_service.api import router as users_router
from core.models.db_helper import db_helper


@asynccontextmanager
async def lifespan(users_app: FastAPI):
    # startup
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as executor:
        await loop.run_in_executor(executor, db_helper.create_db_if_not_exists)

    async with db_helper.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

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
