"""Tests for the catalog service queries."""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.catalog import service
from app.catalog.models import Spell
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
    assert len(classes) == 5


@pytest.mark.asyncio
async def test_list_classes_translated_search(db: AsyncSession) -> None:
    """list_classes_translated with search filters by translated name substring."""
    await seed_catalog(db)
    results = await service.list_classes_translated(db, search="fighter")
    assert all("fighter" in c.name.lower() for c in results)
    assert len(results) == 1


@pytest.mark.asyncio
async def test_get_class_loads_features_and_subclasses(db: AsyncSession) -> None:
    """get_class should load class levels (with features) and subclasses."""
    await seed_catalog(db)
    results = await service.list_classes_translated(db, search="Fighter")
    fighter = await service.get_class(db, results[0].id)

    assert fighter is not None
    assert len(fighter.class_levels) > 0
    assert len(fighter.subclasses) == 3


@pytest.mark.asyncio
async def test_get_class_translated_resolves_full_progression(
    db: AsyncSession,
) -> None:
    """get_class_translated resolves every level 1-20 with features/prerequisites."""
    await seed_catalog(db)
    results = await service.list_classes_translated(db, search="Fighter")
    fighter = await service.get_class_translated(db, results[0].id, locale="en")

    assert fighter is not None
    assert fighter.name == "Fighter"
    assert [level.level for level in fighter.levels] == list(range(1, 21))
    all_features = [f for level in fighter.levels for f in level.features]
    assert any(f.feature_name == "Extra Attack" for f in all_features)
    extra_attack_2 = next(
        f for f in all_features if f.feature_name == "Extra Attack (2)"
    )
    assert len(extra_attack_2.prerequisites) == 1
    assert extra_attack_2.prerequisites[0].prerequisite_type == "feature"
    assert any(sc.name == "Champion" for sc in fighter.subclasses)


@pytest.mark.asyncio
async def test_get_class_translated_falls_back_to_en(db: AsyncSession) -> None:
    """get_class_translated falls back to `en` when the locale has no translation."""
    await seed_catalog(db)
    results = await service.list_classes_translated(db, search="Fighter")
    fighter = await service.get_class_translated(db, results[0].id, locale="pt-BR")

    assert fighter is not None
    assert fighter.name == "Fighter"


@pytest.mark.asyncio
async def test_barbarian_full_progression_with_resources(db: AsyncSession) -> None:
    """Barbarian's 20-level progression carries rage_count/rage_damage resources."""
    await seed_catalog(db)
    results = await service.list_classes_translated(db, search="Barbarian")
    barbarian = await service.get_class_translated(db, results[0].id, locale="en")

    assert barbarian is not None
    assert [level.level for level in barbarian.levels] == list(range(1, 21))
    level_1 = next(level for level in barbarian.levels if level.level == 1)
    resources = {r.resource_key: r.value for r in level_1.resources}
    assert resources["rage_count"] == "2"
    assert resources["rage_damage"] == "+2"
    level_20 = next(level for level in barbarian.levels if level.level == 20)
    resources_20 = {r.resource_key: r.value for r in level_20.resources}
    assert resources_20["rage_count"] == "unlimited"


@pytest.mark.asyncio
async def test_list_spells_filter_by_level(db: AsyncSession) -> None:
    """list_spells with level filter should return only cantrips."""
    await seed_catalog(db)
    cantrips = await service.list_spells(db, level=0)
    assert all(s.level == 0 for s in cantrips)
    assert len(cantrips) == 5


@pytest.mark.asyncio
async def test_list_spells_filter_by_school(db: AsyncSession) -> None:
    """list_spells with school filter should restrict results by MagicSchool index."""
    await seed_catalog(db)
    evocations = await service.list_spells(db, school="evocation")
    assert all(s.magic_school.index == "evocation" for s in evocations)
    assert len(evocations) > 0


@pytest.mark.asyncio
async def test_list_spells_translated_search(db: AsyncSession) -> None:
    """list_spells_translated with search should match translated name substring."""
    await seed_catalog(db)
    results = await service.list_spells_translated(db, search="fire")
    assert all("fire" in s.name.lower() for s in results)
    assert len(results) > 0


@pytest.mark.asyncio
async def test_get_spell_translated_resolves_classes(db: AsyncSession) -> None:
    """get_spell_translated resolves name/description and casting classes."""
    await seed_catalog(db)
    results = await service.list_spells_translated(db, search="Fireball")
    fireball = await service.get_spell_translated(db, results[0].id, locale="en")

    assert fireball is not None
    assert fireball.name == "Fireball"
    assert fireball.school == "evocation"
    assert any(c.name == "Wizard" for c in fireball.classes)


@pytest.mark.asyncio
async def test_get_spell_translated_resolves_multiple_classes(
    db: AsyncSession,
) -> None:
    """A spell castable by more than one class resolves every SpellClass row."""
    await seed_catalog(db)
    results = await service.list_spells_translated(db, search="Detect Magic")
    detect_magic = await service.get_spell_translated(db, results[0].id, locale="en")

    assert detect_magic is not None
    names = {c.name for c in detect_magic.classes}
    assert names == {"Wizard", "Cleric"}


@pytest.mark.asyncio
async def test_list_spells_scoped_to_campaign_includes_srd_and_own_homebrew(
    db: AsyncSession,
) -> None:
    """`list_spells(campaign_id=X)` returns SRD + own campaign homebrew, not others'."""
    await seed_catalog(db)
    srd_spells = await service.list_spells(db)
    magic_school_id = srd_spells[0].magic_school_id

    campaign_a = uuid.uuid4()
    campaign_b = uuid.uuid4()
    homebrew_a = Spell(
        id=uuid.uuid4(),
        index=None,
        level=1,
        magic_school_id=magic_school_id,
        casting_time="1 action",
        range="Self",
        duration="Instantaneous",
        components="V",
        ritual=False,
        concentration=False,
        is_custom=True,
        campaign_id=campaign_a,
    )
    homebrew_b = Spell(
        id=uuid.uuid4(),
        index=None,
        level=1,
        magic_school_id=magic_school_id,
        casting_time="1 action",
        range="Self",
        duration="Instantaneous",
        components="V",
        ritual=False,
        concentration=False,
        is_custom=True,
        campaign_id=campaign_b,
    )
    db.add_all([homebrew_a, homebrew_b])
    await db.commit()

    results = await service.list_spells(db, campaign_id=campaign_a)
    ids = {s.id for s in results}

    assert homebrew_a.id in ids
    assert homebrew_b.id not in ids
    assert {s.id for s in srd_spells} <= ids


@pytest.mark.asyncio
async def test_get_spell_translated_falls_back_to_en(db: AsyncSession) -> None:
    """get_spell_translated falls back to `en` when the locale has no translation."""
    await seed_catalog(db)
    results = await service.list_spells_translated(db, search="Fireball")
    fireball = await service.get_spell_translated(db, results[0].id, locale="pt-BR")

    assert fireball is not None
    assert fireball.name == "Fireball"


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
