"""SQLAlchemy models for the inventory domain: PartyInventory, LootDrop (PRD §7.9)."""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class PartyInventory(Base):
    """One stack of a catalog item shared by the whole party in a campaign."""

    __tablename__ = "party_inventory"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    campaign_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("campaigns.id"))
    item_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("catalog_items.id"))
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    notes: Mapped[str | None] = mapped_column(String(500))


class LootDrop(Base):
    """A drop of loot from an encounter — a catalog/custom item, currency, or both.

    `item_id` and `custom_item_name` are mutually exclusive, enforced in
    `app.inventory.domain.validate_loot_drop_kind` at the application layer
    (mirrors `EncounterParticipant.character_id`/`npc_id`, PRD §7.6).
    """

    __tablename__ = "loot_drops"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    encounter_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("encounters.id"))
    item_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("catalog_items.id")
    )
    custom_item_name: Mapped[str | None] = mapped_column(String(255))
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    currency_cp: Mapped[int] = mapped_column(Integer, default=0)
    claimed_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("characters.id")
    )
