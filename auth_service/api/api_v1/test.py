from fastapi import (
    APIRouter, Request,
)

router = APIRouter(prefix="/test", tags=["TEST"])


@router.get("/set_session")
async def set_session(request: Request):
    """
    Тестирование cookies
    """
    request.session["test_key"] = "test_value"
    return {"message": "Session set"}


@router.get("/get_session")
async def get_session(request: Request):
    """
    Тестирование cookies
    """
    value = request.session.get("test_key", "not found")
    return {"session_value": value}