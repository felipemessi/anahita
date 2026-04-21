"""Pydantic request/response schemas for auth endpoints."""

import uuid

from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    """Payload for POST /auth/register."""

    email: EmailStr
    username: str
    password: str


class LoginRequest(BaseModel):
    """Payload for POST /auth/login."""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Response body for login and token refresh."""

    access_token: str
    token_type: str = "bearer"


class UserPublic(BaseModel):
    """Safe public representation of a user (no password hash)."""

    id: uuid.UUID
    email: str
    username: str

    model_config = {"from_attributes": True}
