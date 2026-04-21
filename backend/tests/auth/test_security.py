"""Unit tests for core security utilities (no database required)."""

import time

import jwt
import pytest

from app.core.security import (
    create_access_token,
    decode_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)


def test_hash_and_verify_password() -> None:
    """Hashed password must verify against the original plain text."""
    hashed = hash_password("secret123")
    assert verify_password("secret123", hashed)
    assert not verify_password("wrong", hashed)


def test_hash_password_is_unique() -> None:
    """Two hashes of the same password must differ (bcrypt salt)."""
    assert hash_password("abc") != hash_password("abc")


def test_create_and_decode_access_token() -> None:
    """Decoded token must carry the original user_id as 'sub'."""
    token = create_access_token("user-abc")
    payload = decode_token(token)
    assert payload["sub"] == "user-abc"
    assert payload["type"] == "access"


def test_decode_token_rejects_tampered() -> None:
    """A modified token must raise InvalidTokenError."""
    token = create_access_token("user-abc")
    tampered = token[:-4] + "xxxx"
    with pytest.raises(jwt.InvalidTokenError):
        decode_token(tampered)


def test_generate_refresh_token_pair() -> None:
    """Raw token must hash to the companion hash via SHA-256."""
    raw, hashed = generate_refresh_token()
    assert hash_refresh_token(raw) == hashed


def test_refresh_tokens_are_unique() -> None:
    """Consecutive calls must return different token pairs."""
    raw1, _ = generate_refresh_token()
    raw2, _ = generate_refresh_token()
    assert raw1 != raw2
