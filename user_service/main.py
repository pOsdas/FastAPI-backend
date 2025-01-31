import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI

from core.config import settings
from users.views import router as users_router
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
main_app.include_router(router=users_router, prefix=settings.api.prefix)


@main_app.get("/")
def hello_index():
    return {
        "message": "Hello from User-Service"
    }


@main_app.get("/hello/")
def hello(name: str = "World"):
    name = name.strip().title()
    return {"message": f"Hello, {name}!"}


if __name__ == "__main__":
    uvicorn.run("main:main_app", reload=True)
