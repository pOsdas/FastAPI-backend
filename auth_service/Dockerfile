FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    gcc \
    libffi-dev \
    libpq-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml poetry.lock* ./

RUN pip install --no-cache-dir "poetry==1.8.2" && \
    poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --only main

COPY . .

EXPOSE 8001

CMD ["poetry", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
