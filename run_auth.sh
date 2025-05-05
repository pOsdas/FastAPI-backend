#!/bin/bash
cd auth_service
PYTHONPATH=$(pwd)/.. poetry run uvicorn main:auth_app --host 127.0.0.1 --port 8001 --reload
