from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, Request, HTTPException
import httpx

from auth_service.core.config import settings


oauth = OAuth()


oauth.register(
    name="google",
    client_id=settings.google_client_id,
    client_secret=settings.google_client_secret,
    authorize_url="https://accounts.google.com/o/oauth2/auth",
    authorize_params={"scope": "openid email profile"},
    access_token_url="https://oauth2.googleapis.com/token",
    access_token_params=None,
    client_kwargs={"scope": "openid email profile"},
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
)

oauth_router = APIRouter(
    prefix="/oauth",
    tags=["OAUTH2"],
)


@oauth_router.get("/login/google")
async def login_google(request: Request):
    """
    Не работает при использовании через Swagger.
    """
    redirect_uri = settings.oauth_redirect_uri
    print("Сессия до авторизации:", request.session)
    response = await oauth.google.authorize_redirect(
        request,
        redirect_uri,
        scope="openid email profile",
        prompt="consent"
    )
    print("Сессия после авторизации:", request.session)
    print("Response:", response)
    return response


@oauth_router.get("/callback/google")
async def callback_google(request: Request):
    """
    Не работает при использовании через Swagger.
    """
    token = await oauth.google.authorize_access_token(request)
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://www.googleapis.com/oauth2/v1/userinfo",
            headers={"Authorization": f"Bearer {token['access_token']}"}
        )
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail="Ошибка получения данных пользователя")
    user_info = resp.json()
    return {"user": user_info}
