from datetime import datetime

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from pydantic import BaseModel, EmailStr, Field

from app.auth.dependencies import get_auth_service, get_current_user
from app.auth.service import AuthService
from app.config.settings import settings

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=256)


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=256)
    full_name: str | None = Field(default=None, max_length=256)


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: str | None = None
    role: str
    is_active: bool


class LoginResponse(BaseModel):
    user: UserResponse


def _set_auth_cookies(
    response: Response,
    session_token: str,
    csrf_token: str,
    expires_at: datetime,
) -> None:
    max_age = max(0, int(expires_at.timestamp() - datetime.now(expires_at.tzinfo).timestamp()))
    cookie_kwargs = {
        "secure": settings.effective_session_cookie_secure,
        "samesite": settings.session_cookie_samesite,
        "max_age": max_age,
        "path": "/",
    }
    response.set_cookie(
        settings.session_cookie_name,
        session_token,
        httponly=True,
        **cookie_kwargs,
    )
    response.set_cookie(
        settings.csrf_cookie_name,
        csrf_token,
        httponly=False,
        **cookie_kwargs,
    )


def _clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(settings.session_cookie_name, path="/")
    response.delete_cookie(settings.csrf_cookie_name, path="/")


@router.post("/register", response_model=LoginResponse, status_code=status.HTTP_201_CREATED)
def register(
    body: RegisterRequest,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
) -> LoginResponse:
    user = auth_service.register_user(body.email, body.password, body.full_name)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists.",
        )

    session_token, csrf_token, expires_at = auth_service.create_session(user["id"])
    _set_auth_cookies(response, session_token, csrf_token, expires_at)
    return LoginResponse(user=UserResponse(**user))


@router.post("/login", response_model=LoginResponse)
def login(
    body: LoginRequest,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
) -> LoginResponse:
    user = auth_service.authenticate_user(body.email, body.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    session_token, csrf_token, expires_at = auth_service.create_session(user["id"])
    _set_auth_cookies(response, session_token, csrf_token, expires_at)
    return LoginResponse(user=UserResponse(**user))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    response: Response,
    session_token: str | None = Cookie(default=None, alias=settings.session_cookie_name),
    auth_service: AuthService = Depends(get_auth_service),
) -> Response:
    if session_token:
        auth_service.revoke_session(session_token)
    _clear_auth_cookies(response)
    return response


@router.get("/me", response_model=UserResponse)
def me(user: dict = Depends(get_current_user)) -> UserResponse:
    return UserResponse(**user)
