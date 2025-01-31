from fastapi import APIRouter, HTTPException, status

from .schemas import CreateUser
from . import crud

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.post("/")
def create_user(user: CreateUser):
    try:
        return crud.create_user(user_in=user)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
