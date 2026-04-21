"""Email + password authentication strategy with JWT and httpOnly refresh token."""

from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import RefreshToken, User
from app.auth.strategies.base import AuthStrategy
from app.config import settings
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_refresh_token,
    verify_password,
)


class LocalAuthStrategy(AuthStrategy):
    """Authenticates via email + bcrypt password; issues JWT + refresh token."""

    async def authenticate(self, email: str, password: str, db: AsyncSession) -> User:
        """Return User if credentials are valid, else raise 401."""
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user

    async def issue_tokens(self, user: User, db: AsyncSession) -> tuple[str, str]:
        """Create a JWT access token and persist a hashed refresh token."""
        access = create_access_token(str(user.id))
        raw, hashed = generate_refresh_token()
        expires = datetime.now(UTC) + timedelta(
            days=settings.refresh_token_expire_days
        )
        db.add(RefreshToken(user_id=user.id, hashed_token=hashed, expires_at=expires))
        return access, raw

    async def refresh_token(self, raw_token: str, db: AsyncSession) -> tuple[str, str]:
        """Rotate: delete old refresh token, issue new access + refresh pair."""
        hashed = hash_refresh_token(raw_token)
        now = datetime.now(UTC)
        result = await db.execute(
            select(RefreshToken).where(
                RefreshToken.hashed_token == hashed,
                RefreshToken.expires_at > now,
            )
        )
        token_row = result.scalar_one_or_none()
        if not token_row:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
            )
        await db.delete(token_row)
        user_result = await db.execute(select(User).where(User.id == token_row.user_id))
        user = user_result.scalar_one()

        access = create_access_token(str(user.id))
        raw_new, hashed_new = generate_refresh_token()
        expires = datetime.now(UTC) + timedelta(
            days=settings.refresh_token_expire_days
        )
        db.add(
            RefreshToken(user_id=user.id, hashed_token=hashed_new, expires_at=expires)
        )
        return access, raw_new

    async def revoke_token(self, raw_token: str, db: AsyncSession) -> None:
        """Delete the refresh token row if it exists."""
        hashed = hash_refresh_token(raw_token)
        result = await db.execute(
            select(RefreshToken).where(RefreshToken.hashed_token == hashed)
        )
        token_row = result.scalar_one_or_none()
        if token_row:
            await db.delete(token_row)
