import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI

from core.config import settings
from user_service.api.api_v1.users import router as auth_router
from core.models.db_helper import db_helper


@asynccontextmanager
async def lifespan(main_app: FastAPI):
    # startup
    yield
    # shutdown
    await db_helper.dispose()


main_app = FastAPI(
    lifespan=lifespan
)
main_app.include_router(router=auth_router, prefix=settings.api.prefix)


@main_app.get("/auth_service")
def hello_index():
    return {
        "message": "Hello from Auth-Service"
    }


if __name__ == "__main__":
    uvicorn.run("main:main_app", reload=True)
