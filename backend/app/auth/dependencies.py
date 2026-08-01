from typing import Annotated

from fastapi import Cookie, Depends, Header, HTTPException, Request, status
from sqlalchemy.engine import Engine

from app.auth.service import AuthService
from app.config.settings import settings
from app.services.database import get_engine

UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def get_auth_service(engine: Engine = Depends(get_engine)) -> AuthService:
    return AuthService(engine)


async def get_current_user(
    session_token: Annotated[str | None, Cookie(alias=settings.session_cookie_name)] = None,
    auth_service: AuthService = Depends(get_auth_service),
) -> dict:
    user = auth_service.get_user_for_session(session_token or "")
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    return user


async def require_csrf(
    request: Request,
    session_token: Annotated[str | None, Cookie(alias=settings.session_cookie_name)] = None,
    csrf_cookie: Annotated[str | None, Cookie(alias=settings.csrf_cookie_name)] = None,
    csrf_header: Annotated[str | None, Header(alias=settings.csrf_header_name)] = None,
    auth_service: AuthService = Depends(get_auth_service),
) -> None:
    if request.method.upper() not in UNSAFE_METHODS:
        return
    if not session_token or not csrf_cookie or not csrf_header:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF token required",
        )
    if csrf_cookie != csrf_header or not auth_service.validate_csrf(session_token, csrf_header):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid CSRF token",
        )
