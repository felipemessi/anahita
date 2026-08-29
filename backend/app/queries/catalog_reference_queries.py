"""Cross-domain reference checks for catalog homebrew deletion (backlog Fase 11).

Each function answers "is this catalog entity still referenced by data
outside the catalog domain?" — used by `catalog.router`'s `DELETE` endpoints
to block deleting homebrew that's still in use (409 Conflict), rather than
leaving another domain with a dangling/orphaned foreign key. See
`docs/anahita-backend-backlog.md` Fase 11 for the policy rationale.

Backgrounds, feats, and rules have no query here: nothing outside the
catalog domain references them (`Character.background` is free text, not a
foreign key), so their delete endpoints skip the reference check entirely.
"""

import uuid
from typing import Any

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.characters.models import (
    Character,
    CharacterClass,
    CharacterEquipment,
    CharacterSpell,
)
from app.combat.models import EncounterParticipant
from app.inventory.models import LootDrop, PartyInventory
from app.world.models import NPC


async def _any(session: AsyncSession, stmt: Select[Any]) -> bool:
    result = await session.execute(stmt)
    return result.first() is not None


async def race_is_referenced(session: AsyncSession, race_id: uuid.UUID) -> bool:
    """Return True if any character has this race (`Character.race_id`)."""
    return await _any(
        session, select(Character.id).where(Character.race_id == race_id).limit(1)
    )


async def class_is_referenced(
    session: AsyncSession, class_definition_id: uuid.UUID
) -> bool:
    """Return True if any character has levels in this class (`CharacterClass`)."""
    return await _any(
        session,
        select(CharacterClass.id)
        .where(CharacterClass.class_definition_id == class_definition_id)
        .limit(1),
    )


async def spell_is_referenced(session: AsyncSession, spell_id: uuid.UUID) -> bool:
    """Return True if any character knows/prepares or is concentrating on this spell."""
    known = await _any(
        session,
        select(CharacterSpell.id).where(CharacterSpell.spell_id == spell_id).limit(1),
    )
    if known:
        return True
    return await _any(
        session,
        select(Character.id)
        .where(Character.concentrating_spell_id == spell_id)
        .limit(1),
    )


async def item_is_referenced(session: AsyncSession, item_id: uuid.UUID) -> bool:
    """Return True if a character carries this item, or a party/loot record uses it."""
    checks = (
        select(CharacterEquipment.id)
        .where(CharacterEquipment.item_id == item_id)
        .limit(1),
        select(PartyInventory.id).where(PartyInventory.item_id == item_id).limit(1),
        select(LootDrop.id).where(LootDrop.item_id == item_id).limit(1),
    )
    for stmt in checks:
        if await _any(session, stmt):
            return True
    return False


async def magic_item_is_referenced(
    session: AsyncSession, magic_item_id: uuid.UUID
) -> bool:
    """Return True if any loot drop references this magic item."""
    return await _any(
        session,
        select(LootDrop.id).where(LootDrop.magic_item_id == magic_item_id).limit(1),
    )


async def monster_is_referenced(session: AsyncSession, monster_id: uuid.UUID) -> bool:
    """Return True if any encounter participant or NPC stat block uses this monster."""
    checks = (
        select(EncounterParticipant.id)
        .where(EncounterParticipant.monster_id == monster_id)
        .limit(1),
        select(NPC.id).where(NPC.stat_block_id == monster_id).limit(1),
    )
    for stmt in checks:
        if await _any(session, stmt):
            return True
    return False
