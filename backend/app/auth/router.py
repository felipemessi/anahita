"""Auth endpoints: register, login, refresh, logout."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.auth.schemas import LoginRequest, RegisterRequest, TokenResponse, UserPublic
from app.auth.service import AuthService
from app.auth.strategies.local import LocalAuthStrategy
from app.core.dependencies import get_current_user
from app.database import get_db

_REFRESH_COOKIE = "refresh_token"
_COOKIE_MAX_AGE = 60 * 60 * 24 * 30

router = APIRouter(prefix="/auth", tags=["auth"])


def get_auth_service() -> AuthService:
    """Return AuthService wired with the local strategy."""
    return AuthService(LocalAuthStrategy())


@router.post(
    "/register",
    response_model=UserPublic,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    body: RegisterRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserPublic:
    """Register a new user account and return the public user profile."""
    user = await service.register(body, db)
    return UserPublic.model_validate(user)


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    """Authenticate with email + password; set refresh token cookie."""
    access, refresh = await service.login(body.email, body.password, db)
    response.set_cookie(
        key=_REFRESH_COOKIE,
        value=refresh,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=_COOKIE_MAX_AGE,
    )
    return TokenResponse(access_token=access)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
    service: Annotated[AuthService, Depends(get_auth_service)],
    refresh_token: Annotated[str | None, Cookie(alias=_REFRESH_COOKIE)] = None,
) -> TokenResponse:
    """Rotate refresh token and issue a new access token."""
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing refresh token",
        )
    access, new_refresh = await service.refresh(refresh_token, db)
    response.set_cookie(
        key=_REFRESH_COOKIE,
        value=new_refresh,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=_COOKIE_MAX_AGE,
    )
    return TokenResponse(access_token=access)


@router.get("/me", response_model=UserPublic)
async def me(
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserPublic:
    """Return the public profile of the currently authenticated user."""
    return UserPublic.model_validate(current_user)


@router.get("/users", response_model=list[UserPublic])
async def list_users(
    db: Annotated[AsyncSession, Depends(get_db)],
    service: Annotated[AuthService, Depends(get_auth_service)],
    _current_user: Annotated[User, Depends(get_current_user)],
    ids: Annotated[
        list[uuid.UUID],
        Query(description="Repeat for each id, e.g. ?ids=<uuid>&ids=<uuid>"),
    ],
) -> list[UserPublic]:
    """Resolve public profiles for a batch of user ids (e.g. campaign member names)."""
    users = await service.list_users_by_ids(ids, db)
    return [UserPublic.model_validate(u) for u in users]


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
    service: Annotated[AuthService, Depends(get_auth_service)],
    refresh_token: Annotated[str | None, Cookie(alias=_REFRESH_COOKIE)] = None,
) -> None:
    """Revoke refresh token and clear the cookie."""
    if refresh_token:
        await service.logout(refresh_token, db)
    response.delete_cookie(key=_REFRESH_COOKIE)
