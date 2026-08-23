"""Integration tests for the auth HTTP endpoints (register/login/refresh)."""

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import app.auth.models  # noqa: F401 — registers models with Base
from app.database import Base, get_db
from app.main import app as fastapi_app

_TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient]:
    """Provide an httpx client wired to the FastAPI app with an isolated DB."""
    engine = create_async_engine(_TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async def _override_get_db() -> AsyncGenerator[AsyncSession]:
        async with factory() as session:
            yield session

    fastapi_app.dependency_overrides[get_db] = _override_get_db
    try:
        transport = ASGITransport(app=fastapi_app)
        async with AsyncClient(transport=transport, base_url="https://test") as ac:
            yield ac
    finally:
        fastapi_app.dependency_overrides.pop(get_db, None)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await engine.dispose()


async def test_full_register_login_refresh_flow(client: AsyncClient) -> None:
    """A user can register, log in, and refresh their access token over HTTP."""
    register_resp = await client.post(
        "/auth/register",
        json={"email": "ada@example.com", "username": "ada", "password": "pass1234"},
    )
    assert register_resp.status_code == 201
    body = register_resp.json()
    assert body["email"] == "ada@example.com"
    assert body["username"] == "ada"
    assert "hashed_password" not in body

    login_resp = await client.post(
        "/auth/login",
        json={"email": "ada@example.com", "password": "pass1234"},
    )
    assert login_resp.status_code == 200
    access_token = login_resp.json()["access_token"]
    assert access_token
    assert "refresh_token" in login_resp.cookies

    refresh_resp = await client.post("/auth/refresh")
    assert refresh_resp.status_code == 200
    new_access_token = refresh_resp.json()["access_token"]
    assert new_access_token
    # Note: access tokens carry only sub+exp+type, so two issued within the same
    # second are byte-identical — refresh token rotation is what we actually verify.

    # Old refresh cookie has been rotated; reusing it must fail.
    old_refresh_cookie = login_resp.cookies["refresh_token"]
    client.cookies.set("refresh_token", old_refresh_cookie)
    stale_refresh_resp = await client.post("/auth/refresh")
    assert stale_refresh_resp.status_code == 401


async def test_register_duplicate_email_returns_409(client: AsyncClient) -> None:
    """Registering twice with the same email returns a conflict over HTTP."""
    payload = {"email": "dup@example.com", "username": "dup", "password": "pass1234"}
    first = await client.post("/auth/register", json=payload)
    assert first.status_code == 201
    second = await client.post("/auth/register", json={**payload, "username": "dup2"})
    assert second.status_code == 409


async def test_login_wrong_password_returns_401(client: AsyncClient) -> None:
    """Logging in with the wrong password returns 401 over HTTP."""
    await client.post(
        "/auth/register",
        json={"email": "eve@example.com", "username": "eve", "password": "correct"},
    )
    resp = await client.post(
        "/auth/login",
        json={"email": "eve@example.com", "password": "wrong"},
    )
    assert resp.status_code == 401


async def test_refresh_without_cookie_returns_401(client: AsyncClient) -> None:
    """Calling refresh with no refresh token cookie returns 401."""
    resp = await client.post("/auth/refresh")
    assert resp.status_code == 401


async def test_me_returns_authenticated_user_profile(client: AsyncClient) -> None:
    """GET /auth/me returns the profile of the user identified by the bearer token."""
    await client.post(
        "/auth/register",
        json={
            "email": "grace@example.com",
            "username": "grace",
            "password": "pass1234",
        },
    )
    login_resp = await client.post(
        "/auth/login",
        json={"email": "grace@example.com", "password": "pass1234"},
    )
    access_token = login_resp.json()["access_token"]

    me_resp = await client.get(
        "/auth/me", headers={"Authorization": f"Bearer {access_token}"}
    )
    assert me_resp.status_code == 200
    body = me_resp.json()
    assert body["email"] == "grace@example.com"
    assert body["username"] == "grace"
    assert "hashed_password" not in body


async def test_me_without_token_returns_401(client: AsyncClient) -> None:
    """GET /auth/me without a bearer token returns 401."""
    resp = await client.get("/auth/me")
    assert resp.status_code == 401


async def test_me_with_invalid_token_returns_401(client: AsyncClient) -> None:
    """GET /auth/me with a malformed/expired token returns 401."""
    resp = await client.get(
        "/auth/me", headers={"Authorization": "Bearer not-a-real-token"}
    )
    assert resp.status_code == 401


async def test_logout_clears_cookie_and_invalidates_refresh(
    client: AsyncClient,
) -> None:
    """Logout revokes the refresh token and clears the cookie."""
    await client.post(
        "/auth/register",
        json={"email": "dave@example.com", "username": "dave", "password": "pw123456"},
    )
    login_resp = await client.post(
        "/auth/login",
        json={"email": "dave@example.com", "password": "pw123456"},
    )
    assert login_resp.status_code == 200

    logout_resp = await client.post("/auth/logout")
    assert logout_resp.status_code == 204

    refresh_resp = await client.post("/auth/refresh")
    assert refresh_resp.status_code == 401
