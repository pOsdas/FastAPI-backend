from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncEngine,
    async_sessionmaker,
    AsyncSession
)

from auth_service.core.config import settings


class DatabaseHelper:
    def __init__(
            self,
            url: str,
            echo: bool = False,
            echo_pool: bool = False,
            pool_pre_ping: bool = True,
            max_overflow: int = 10,
            pool_size: int = 5,
    ) -> None:
        self.engine: AsyncEngine = create_async_engine(
            url=url,
            echo=echo,
            echo_pool=echo_pool,
            pool_pre_ping=pool_pre_ping,
            max_overflow=max_overflow,
            pool_size=pool_size,
        )
        self.session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
            bind=self.engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )

    async def dispose(self) -> None:
        await self.engine.dispose()

    async def session_getter(self) -> AsyncGenerator[AsyncSession, None]:
        async with self.session_factory() as session:
            yield session

    @staticmethod
    def create_db_if_not_exists():
        import psycopg2
        from urllib.parse import urlparse

        parsed = urlparse(str(settings.db.url))
        target_db = parsed.path.lstrip("/")
        user = parsed.username
        password = parsed.password
        host = parsed.hostname
        port = parsed.port

        conn = psycopg2.connect(dbname="postgres", user=user, password=password, host=host, port=port)
        conn.autocommit = True
        cur = conn.cursor()

        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (target_db,))
        exists = cur.fetchone()

        if not exists:
            print(f"База данных '{target_db}' не найдена. Создаю...")
            cur.execute(f"CREATE DATABASE {target_db}")
        else:
            print(f"База данных '{target_db}' уже существует.")

        cur.close()
        conn.close()


db_helper = DatabaseHelper(
    url=str(settings.db.url),
    echo=settings.db.echo,
    echo_pool=settings.db.echo_pool,
    pool_pre_ping=settings.db.pool_pre_ping,
    pool_size=settings.db.pool_size,
    max_overflow=settings.db.max_overflow,
)
