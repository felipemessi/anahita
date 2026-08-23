"""Tests for the catalog seed function."""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.catalog import service
from app.catalog.models import ClassDefinition, Item, Race, Spell
from app.catalog.seeds.seed import seed_catalog


@pytest.mark.asyncio
async def test_seed_creates_races(db: AsyncSession) -> None:
    """seed_catalog should insert all four SRD races."""
    await seed_catalog(db)

    races = (await db.execute(select(Race).order_by(Race.index))).scalars().all()
    indexes = {r.index for r in races}
    assert indexes == {"dwarf", "elf", "halfling", "human"}

    summaries = await service.list_races_translated(db)
    names = {r.name for r in summaries}
    assert names == {"Dwarf", "Elf", "Halfling", "Human"}


@pytest.mark.asyncio
async def test_seed_creates_classes(db: AsyncSession) -> None:
    """seed_catalog should insert the five SRD classes."""
    await seed_catalog(db)

    classes = (
        (await db.execute(select(ClassDefinition).order_by(ClassDefinition.index)))
        .scalars()
        .all()
    )
    indexes = {c.index for c in classes}
    assert indexes == {"barbarian", "cleric", "fighter", "rogue", "wizard"}

    summaries = await service.list_classes_translated(db)
    names = {c.name for c in summaries}
    assert names == {"Barbarian", "Cleric", "Fighter", "Rogue", "Wizard"}


@pytest.mark.asyncio
async def test_seed_creates_spells(db: AsyncSession) -> None:
    """seed_catalog should insert 20 SRD spells."""
    await seed_catalog(db)

    spells = (await db.execute(select(Spell))).scalars().all()
    assert len(spells) == 20


@pytest.mark.asyncio
async def test_seed_creates_items(db: AsyncSession) -> None:
    """seed_catalog should insert SRD items."""
    await seed_catalog(db)

    items = (await db.execute(select(Item))).scalars().all()
    assert len(items) > 0


@pytest.mark.asyncio
async def test_seed_is_idempotent(db: AsyncSession) -> None:
    """Running seed_catalog twice should not duplicate rows."""
    await seed_catalog(db)
    await seed_catalog(db)

    spells = (await db.execute(select(Spell))).scalars().all()
    assert len(spells) == 20
