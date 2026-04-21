"""Integration tests for AuthService using SQLite in-memory database."""

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.schemas import RegisterRequest
from app.auth.service import AuthService
from app.auth.strategies.local import LocalAuthStrategy


def _service() -> AuthService:
    return AuthService(LocalAuthStrategy())


@pytest.fixture
def service() -> AuthService:
    """Return an AuthService backed by LocalAuthStrategy."""
    return _service()


async def test_register_creates_user(db: AsyncSession, service: AuthService) -> None:
    """Register returns a User with the correct email and username."""
    req = RegisterRequest(email="ada@example.com", username="ada", password="pass1234")
    user = await service.register(req, db)
    assert user.email == "ada@example.com"
    assert user.username == "ada"
    assert user.hashed_password != "pass1234"


async def test_register_duplicate_email_raises(
    db: AsyncSession, service: AuthService
) -> None:
    """Registering with an existing email must raise 409."""
    req = RegisterRequest(email="dup@example.com", username="user1", password="pass")
    await service.register(req, db)
    req2 = RegisterRequest(email="dup@example.com", username="user2", password="pass")
    with pytest.raises(HTTPException) as exc:
        await service.register(req2, db)
    assert exc.value.status_code == 409


async def test_register_duplicate_username_raises(
    db: AsyncSession, service: AuthService
) -> None:
    """Registering with an existing username must raise 409."""
    req = RegisterRequest(email="a@example.com", username="taken", password="pass")
    await service.register(req, db)
    req2 = RegisterRequest(email="b@example.com", username="taken", password="pass")
    with pytest.raises(HTTPException) as exc:
        await service.register(req2, db)
    assert exc.value.status_code == 409


async def test_login_returns_tokens(db: AsyncSession, service: AuthService) -> None:
    """Successful login returns non-empty access and refresh tokens."""
    req = RegisterRequest(email="bob@example.com", username="bob", password="securepass")
    await service.register(req, db)
    access, refresh = await service.login("bob@example.com", "securepass", db)
    assert access
    assert refresh


async def test_login_wrong_password_raises(
    db: AsyncSession, service: AuthService
) -> None:
    """Login with wrong password must raise 401."""
    req = RegisterRequest(email="eve@example.com", username="eve", password="correct")
    await service.register(req, db)
    with pytest.raises(HTTPException) as exc:
        await service.login("eve@example.com", "wrong", db)
    assert exc.value.status_code == 401


async def test_login_unknown_email_raises(
    db: AsyncSession, service: AuthService
) -> None:
    """Login with unknown email must raise 401."""
    with pytest.raises(HTTPException) as exc:
        await service.login("ghost@example.com", "pass", db)
    assert exc.value.status_code == 401


async def test_refresh_rotates_token(db: AsyncSession, service: AuthService) -> None:
    """Refresh returns new tokens and the old refresh token becomes invalid."""
    req = RegisterRequest(email="carol@example.com", username="carol", password="pw")
    await service.register(req, db)
    _, refresh = await service.login("carol@example.com", "pw", db)

    new_access, new_refresh = await service.refresh(refresh, db)
    assert new_access
    assert new_refresh != refresh

    with pytest.raises(HTTPException) as exc:
        await service.refresh(refresh, db)
    assert exc.value.status_code == 401


async def test_logout_invalidates_token(db: AsyncSession, service: AuthService) -> None:
    """After logout, the refresh token must no longer be usable."""
    req = RegisterRequest(email="dave@example.com", username="dave", password="pw")
    await service.register(req, db)
    _, refresh = await service.login("dave@example.com", "pw", db)

    await service.logout(refresh, db)

    with pytest.raises(HTTPException) as exc:
        await service.refresh(refresh, db)
    assert exc.value.status_code == 401
