"""AuthService orchestrates registration, login, refresh, and logout."""

import uuid

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.domain import ProviderType
from app.auth.models import AuthProvider, User
from app.auth.schemas import RegisterRequest
from app.auth.strategies.base import AuthStrategy
from app.core.security import hash_password


class AuthService:
    """Orchestrates auth operations using an injected AuthStrategy."""

    def __init__(self, strategy: AuthStrategy) -> None:
        """Inject the concrete authentication strategy."""
        self._strategy = strategy

    async def register(self, request: RegisterRequest, db: AsyncSession) -> User:
        """Create a new user with a local auth provider."""
        conflict = await db.execute(
            select(User).where(
                or_(User.email == request.email, User.username == request.username)
            )
        )
        if conflict.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email or username already in use",
            )
        user = User(
            email=request.email,
            username=request.username,
            hashed_password=hash_password(request.password),
        )
        db.add(user)
        await db.flush()
        db.add(
            AuthProvider(
                user_id=user.id,
                provider_type=ProviderType.local,
                provider_user_id=request.email,
            )
        )
        await db.commit()
        await db.refresh(user)
        return user

    async def login(
        self, email: str, password: str, db: AsyncSession
    ) -> tuple[str, str]:
        """Authenticate and return (access_token, raw_refresh_token)."""
        user = await self._strategy.authenticate(email, password, db)
        access, refresh = await self._strategy.issue_tokens(user, db)
        await db.commit()
        return access, refresh

    async def refresh(self, raw_token: str, db: AsyncSession) -> tuple[str, str]:
        """Rotate refresh token; return (new_access_token, new_raw_refresh_token)."""
        access, new_refresh = await self._strategy.refresh_token(raw_token, db)
        await db.commit()
        return access, new_refresh

    async def logout(self, raw_token: str, db: AsyncSession) -> None:
        """Revoke the given refresh token."""
        await self._strategy.revoke_token(raw_token, db)
        await db.commit()

    async def list_users_by_ids(
        self, ids: list[uuid.UUID], db: AsyncSession
    ) -> list[User]:
        """Return the users matching `ids` (silently skips ids that don't exist)."""
        if not ids:
            return []
        result = await db.execute(select(User).where(User.id.in_(ids)))
        return list(result.scalars().all())
