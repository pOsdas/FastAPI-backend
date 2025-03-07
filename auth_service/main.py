import uvicorn
import asyncio
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.cors import CORSMiddleware

from core.config import settings
from core.models import Base
from auth_service.api import router as auth_router
from core.models.db_helper import db_helper


@asynccontextmanager
async def lifespan(auth_app: FastAPI):
    # startup
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as executor:
        await loop.run_in_executor(executor, db_helper.create_db_if_not_exists)

    async with db_helper.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield
    # shutdown
    await db_helper.dispose()


auth_app = FastAPI(
    lifespan=lifespan
)

auth_app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
    https_only=False,
    same_site="lax",
)
auth_app.add_middleware(
    CORSMiddleware,
    # secret_key=settings.secret_key,
    allow_origins=["http://127.0.0.1:8001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

auth_app.include_router(router=auth_router)


@auth_app.get("/")
def hello_index():
    return {
        "message": "Hello"
    }


@auth_app.get("/auth_service")
def hello_index():
    return {
        "message": "Hello from Auth-Service"
    }


if __name__ == "__main__":
    # print(f"DataBase URL: {settings.db.url}")
    # print(
    #     f"Database settings: "
    #     f"{settings.db.echo}",
    #     f"{settings.db.echo_pool}"
    # )
    # print(f"Google CLIENT_ID: {settings.google_client_id}")
    # print(f"Google CLIENT_SECRET: {settings.google_client_secret}")
    # print(f"OAuth2 REDIRECT_URI: {settings.oauth_redirect_uri}")
    uvicorn.run(
        "main:auth_app",
        host=settings.run.host,
        port=settings.run.port,
        reload=True
    )
