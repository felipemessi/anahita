"""Password hashing and JWT utilities."""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
import jwt

from app.config import settings

ALGORITHM = "HS256"


def hash_password(plain: str) -> str:
    """Return bcrypt hash of plain-text password."""
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if plain matches the stored bcrypt hash."""
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(user_id: str) -> str:
    """Return a short-lived signed JWT access token."""
    expire = datetime.now(UTC) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    return jwt.encode(
        {"sub": user_id, "exp": expire, "type": "access"},
        settings.secret_key,
        algorithm=ALGORITHM,
    )


def decode_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT; raises jwt.InvalidTokenError on failure."""
    payload: dict[str, Any] = jwt.decode(
        token, settings.secret_key, algorithms=[ALGORITHM]
    )
    return payload


def generate_refresh_token() -> tuple[str, str]:
    """Return (raw_token, sha256_hash). Store the hash; send raw in httpOnly cookie."""
    raw = secrets.token_urlsafe(32)
    hashed = hashlib.sha256(raw.encode()).hexdigest()
    return raw, hashed


def hash_refresh_token(raw: str) -> str:
    """Compute SHA-256 of a raw refresh token for database lookup."""
    return hashlib.sha256(raw.encode()).hexdigest()
