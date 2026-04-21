"""Abstract base for authentication strategies."""

from abc import ABC, abstractmethod

from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User


class AuthStrategy(ABC):
    """Contract for pluggable auth backends (local, OAuth2, etc.)."""

    @abstractmethod
    async def authenticate(self, email: str, password: str, db: AsyncSession) -> User:
        """Verify credentials and return the authenticated User."""
        ...

    @abstractmethod
    async def issue_tokens(self, user: User, db: AsyncSession) -> tuple[str, str]:
        """Persist tokens and return (access_token, raw_refresh_token)."""
        ...

    @abstractmethod
    async def refresh_token(self, raw_token: str, db: AsyncSession) -> tuple[str, str]:
        """Rotate refresh token and return (new_access_token, new_raw_refresh_token)."""
        ...

    @abstractmethod
    async def revoke_token(self, raw_token: str, db: AsyncSession) -> None:
        """Invalidate a refresh token (logout)."""
        ...
