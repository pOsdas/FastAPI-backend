#!/bin/bash
cd user_service
PYTHONPATH=$(pwd)/.. poetry run uvicorn main:users_app --host 127.0.0.1 --port 8000 --reload
