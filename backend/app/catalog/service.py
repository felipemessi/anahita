"""Catalog service — read-only queries for SRD reference data."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.catalog.models import (
    ClassDefinition,
    Item,
    Race,
    Spell,
    Subrace,
)


async def list_races(
    session: AsyncSession,
    *,
    search: str | None = None,
    include_custom: bool = True,
) -> list[Race]:
    """Return all races, optionally filtered by name substring."""
    stmt = (
        select(Race)
        .options(
            selectinload(Race.traits),
            selectinload(Race.ability_bonuses),
            selectinload(Race.subraces).selectinload(Subrace.traits),
            selectinload(Race.subraces).selectinload(Subrace.ability_bonuses),
        )
        .order_by(Race.name)
    )
    if search:
        stmt = stmt.where(Race.name.ilike(f"%{search}%"))
    if not include_custom:
        stmt = stmt.where(Race.is_custom.is_(False))
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_race(session: AsyncSession, race_id: uuid.UUID) -> Race | None:
    """Return a single race by ID, or None if not found."""
    stmt = (
        select(Race)
        .where(Race.id == race_id)
        .options(
            selectinload(Race.traits),
            selectinload(Race.ability_bonuses),
            selectinload(Race.subraces).selectinload(Subrace.traits),
            selectinload(Race.subraces).selectinload(Subrace.ability_bonuses),
        )
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def list_classes(
    session: AsyncSession,
    *,
    search: str | None = None,
    include_custom: bool = True,
) -> list[ClassDefinition]:
    """Return all class definitions, optionally filtered by name substring."""
    stmt = (
        select(ClassDefinition)
        .options(
            selectinload(ClassDefinition.level_features),
            selectinload(ClassDefinition.subclasses),
        )
        .order_by(ClassDefinition.name)
    )
    if search:
        stmt = stmt.where(ClassDefinition.name.ilike(f"%{search}%"))
    if not include_custom:
        stmt = stmt.where(ClassDefinition.is_custom.is_(False))
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_class(
    session: AsyncSession, class_id: uuid.UUID
) -> ClassDefinition | None:
    """Return a single class definition by ID, or None if not found."""
    stmt = (
        select(ClassDefinition)
        .where(ClassDefinition.id == class_id)
        .options(
            selectinload(ClassDefinition.level_features),
            selectinload(ClassDefinition.subclasses),
        )
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def list_spells(
    session: AsyncSession,
    *,
    search: str | None = None,
    level: int | None = None,
    school: str | None = None,
) -> list[Spell]:
    """Return all spells, optionally filtered by name, level, or school."""
    stmt = select(Spell).order_by(Spell.level, Spell.name)
    if search:
        stmt = stmt.where(Spell.name.ilike(f"%{search}%"))
    if level is not None:
        stmt = stmt.where(Spell.level == level)
    if school:
        stmt = stmt.where(Spell.school == school)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_spell(session: AsyncSession, spell_id: uuid.UUID) -> Spell | None:
    """Return a single spell by ID, or None if not found."""
    result = await session.execute(select(Spell).where(Spell.id == spell_id))
    return result.scalar_one_or_none()


async def list_items(
    session: AsyncSession,
    *,
    search: str | None = None,
    item_type: str | None = None,
) -> list[Item]:
    """Return all items, optionally filtered by name substring or type."""
    stmt = (
        select(Item)
        .options(
            selectinload(Item.weapon_detail),
            selectinload(Item.armor_detail),
        )
        .order_by(Item.name)
    )
    if search:
        stmt = stmt.where(Item.name.ilike(f"%{search}%"))
    if item_type:
        stmt = stmt.where(Item.item_type == item_type)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_item(session: AsyncSession, item_id: uuid.UUID) -> Item | None:
    """Return a single item by ID, or None if not found."""
    stmt = (
        select(Item)
        .where(Item.id == item_id)
        .options(
            selectinload(Item.weapon_detail),
            selectinload(Item.armor_detail),
        )
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()
