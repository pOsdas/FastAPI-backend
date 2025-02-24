## User Service & Auth Service
## Бэк-енд на микросервисах

- Микросервис **User Service** отвечает за управление пользователями (создание, обновление, поиск)
- Микросервис **Auth Service** обрабатывает аутентификацию, JWT-токены, OAuth 
---
## Запуск User Service
```shell
poetry run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Запуск Auth Service
```shell
poetry run uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

## Библиотеки
- **fastAPI**
- **aiosqlite**
- **bcrypt**
- **authlib**
- **psycopg**
- **aiosmtplib**
- **SQLAlchemy**
- **Alembic**
- **Poetry**
- **Pydantic**
- **Asyncpg**
- **Uvicorn**
- **HTTPX**
- **pyjwt**
- **starlette**
- **itsdangerous**
