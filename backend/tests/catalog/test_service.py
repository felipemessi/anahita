"""Tests for the catalog service queries."""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.catalog import service
from app.catalog.models import (
    ArmorDetail,
    ClassDefinition,
    Item,
    Race,
    Spell,
    WeaponDetail,
)
from app.catalog.seeds.seed import seed_catalog


@pytest.mark.asyncio
async def test_list_races_returns_all(db: AsyncSession) -> None:
    """list_races should return all seeded races."""
    await seed_catalog(db)
    races = await service.list_races(db)
    assert len(races) == 4


@pytest.mark.asyncio
async def test_list_races_translated_search(db: AsyncSession) -> None:
    """list_races_translated with search should filter by translated name substring."""
    await seed_catalog(db)
    results = await service.list_races_translated(db, search="elf")
    assert all("elf" in r.name.lower() for r in results)
    assert len(results) == 1


@pytest.mark.asyncio
async def test_get_race_loads_traits_and_subraces(db: AsyncSession) -> None:
    """get_race should eagerly load traits, subraces and ability bonuses."""
    await seed_catalog(db)
    results = await service.list_races_translated(db, search="Elf")
    elf = await service.get_race(db, results[0].id)

    assert elf is not None
    assert len(elf.traits) > 0
    assert len(elf.subraces) == 2
    assert any(ab.ability == "dex" for ab in elf.ability_bonuses)


@pytest.mark.asyncio
async def test_get_race_translated_resolves_all_text_fields(db: AsyncSession) -> None:
    """get_race_translated should resolve race, trait, and subrace text for `en`."""
    await seed_catalog(db)
    results = await service.list_races_translated(db, search="Elf")
    elf = await service.get_race_translated(db, results[0].id, locale="en")

    assert elf is not None
    assert elf.name == "Elf"
    assert elf.description
    assert elf.age
    assert all(t.trait_name for t in elf.traits)
    assert all(sr.name for sr in elf.subraces)
    assert all(t.trait_name for sr in elf.subraces for t in sr.traits)


@pytest.mark.asyncio
async def test_get_race_translated_falls_back_to_en(db: AsyncSession) -> None:
    """get_race_translated falls back to `en` when the locale has no translation."""
    await seed_catalog(db)
    results = await service.list_races_translated(db, search="Elf")
    elf = await service.get_race_translated(db, results[0].id, locale="pt-BR")

    assert elf is not None
    assert elf.name == "Elf"


@pytest.mark.asyncio
async def test_get_race_not_found_returns_none(db: AsyncSession) -> None:
    """get_race should return None for an unknown ID."""
    result = await service.get_race(db, uuid.uuid4())
    assert result is None


@pytest.mark.asyncio
async def test_get_race_translated_not_found_returns_none(db: AsyncSession) -> None:
    """get_race_translated should return None for an unknown ID."""
    result = await service.get_race_translated(db, uuid.uuid4())
    assert result is None


@pytest.mark.asyncio
async def test_list_classes_returns_all(db: AsyncSession) -> None:
    """list_classes should return all seeded classes."""
    await seed_catalog(db)
    classes = await service.list_classes(db)
    assert len(classes) == 4


@pytest.mark.asyncio
async def test_get_class_loads_features_and_subclasses(db: AsyncSession) -> None:
    """get_class should load level features and subclasses."""
    await seed_catalog(db)
    classes = await service.list_classes(db, search="Fighter")
    fighter = await service.get_class(db, classes[0].id)

    assert fighter is not None
    assert len(fighter.level_features) > 0
    assert len(fighter.subclasses) == 3


@pytest.mark.asyncio
async def test_list_spells_filter_by_level(db: AsyncSession) -> None:
    """list_spells with level filter should return only cantrips."""
    await seed_catalog(db)
    cantrips = await service.list_spells(db, level=0)
    assert all(s.level == 0 for s in cantrips)
    assert len(cantrips) == 5


@pytest.mark.asyncio
async def test_list_spells_filter_by_school(db: AsyncSession) -> None:
    """list_spells with school filter should restrict results."""
    await seed_catalog(db)
    evocations = await service.list_spells(db, school="evocation")
    assert all(s.school == "evocation" for s in evocations)
    assert len(evocations) > 0


@pytest.mark.asyncio
async def test_list_spells_search(db: AsyncSession) -> None:
    """list_spells with search should match name substring."""
    await seed_catalog(db)
    results = await service.list_spells(db, search="fire")
    assert all("fire" in s.name.lower() for s in results)


@pytest.mark.asyncio
async def test_list_items_filter_by_type(db: AsyncSession) -> None:
    """list_items with item_type filter should restrict results."""
    await seed_catalog(db)
    weapons = await service.list_items(db, item_type="weapon")
    assert all(i.item_type == "weapon" for i in weapons)
    assert len(weapons) > 0


@pytest.mark.asyncio
async def test_get_item_loads_weapon_detail(db: AsyncSession) -> None:
    """get_item should load weapon_detail for weapon items."""
    await seed_catalog(db)
    items = await service.list_items(db, search="Longsword")
    longsword = await service.get_item(db, items[0].id)

    assert longsword is not None
    assert longsword.weapon_detail is not None
    assert longsword.weapon_detail.damage_dice == "1d8"


@pytest.mark.asyncio
async def test_get_item_loads_armor_detail(db: AsyncSession) -> None:
    """get_item should load armor_detail for armor items."""
    await seed_catalog(db)
    items = await service.list_items(db, search="Leather Armor")
    armor = await service.get_item(db, items[0].id)

    assert armor is not None
    assert armor.armor_detail is not None
    assert armor.armor_detail.base_ac == 11


@pytest.mark.asyncio
async def test_get_item_not_found_returns_none(db: AsyncSession) -> None:
    """get_item should return None for an unknown ID."""
    result = await service.get_item(db, uuid.uuid4())
    assert result is None
