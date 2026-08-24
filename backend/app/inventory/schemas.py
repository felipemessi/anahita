"""Pydantic request/response schemas for the inventory domain."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, Field


class PartyInventoryCreate(BaseModel):
    """Request body to add a stack of an item to the party inventory."""

    item_id: uuid.UUID
    quantity: int = Field(default=1, ge=1)
    notes: str | None = None


class PartyInventoryUpdate(BaseModel):
    """Request body to adjust a party inventory entry's quantity/notes."""

    quantity: int | None = Field(default=None, ge=0)
    notes: str | None = None


class PartyInventoryRead(BaseModel):
    """Response schema for a party inventory entry."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    campaign_id: uuid.UUID
    item_id: uuid.UUID
    quantity: int
    notes: str | None


class LootDropCreate(BaseModel):
    """Request body to record a loot drop from an encounter.

    `item_id`, `magic_item_id`, and `custom_item_name` are mutually
    exclusive — see `app.inventory.domain.validate_loot_drop_kind`.
    """

    item_id: uuid.UUID | None = None
    magic_item_id: uuid.UUID | None = None
    custom_item_name: str | None = Field(default=None, max_length=255)
    quantity: int = Field(default=1, ge=1)
    currency_cp: int = Field(default=0, ge=0)


class LootDropRead(BaseModel):
    """Response schema for a loot drop."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    encounter_id: uuid.UUID
    item_id: uuid.UUID | None
    magic_item_id: uuid.UUID | None
    custom_item_name: str | None
    quantity: int
    currency_cp: int
    claimed_by: uuid.UUID | None


class LootDropClaim(BaseModel):
    """Request body to claim a loot drop for a character."""

    character_id: uuid.UUID
