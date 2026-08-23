"""Tests for the catalog service queries."""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.catalog import service
from app.catalog.models import (
    AbilityScoreDefinition,
    Background,
    BackgroundProficiency,
    Feat,
    FeatPrerequisite,
    Item,
    MagicItem,
    Proficiency,
    Spell,
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
async def test_list_items_translated_search(db: AsyncSession) -> None:
    """list_items_translated with search should match translated name substring."""
    await seed_catalog(db)
    results = await service.list_items_translated(db, search="Longsword")
    assert all("longsword" in i.name.lower() for i in results)
    assert len(results) > 0


@pytest.mark.asyncio
async def test_get_item_translated_resolves_weapon_detail_and_properties(
    db: AsyncSession,
) -> None:
    """get_item_translated resolves weapon_detail (damage_type) and properties."""
    await seed_catalog(db)
    results = await service.list_items_translated(db, search="Longsword")
    longsword = await service.get_item_translated(db, results[0].id, locale="en")

    assert longsword is not None
    assert longsword.name == "Longsword"
    assert longsword.weapon_detail is not None
    assert longsword.weapon_detail.damage_dice == "1d8"
    assert longsword.weapon_detail.damage_type == "slashing"
    assert any(p.name == "Versatile" for p in longsword.properties)


@pytest.mark.asyncio
async def test_get_item_translated_resolves_multiple_properties(
    db: AsyncSession,
) -> None:
    """An item with several weapon properties resolves every ItemProperty row."""
    await seed_catalog(db)
    results = await service.list_items_translated(db, search="Dagger")
    dagger = await service.get_item_translated(db, results[0].id, locale="en")

    assert dagger is not None
    names = {p.name for p in dagger.properties}
    assert names == {"Finesse", "Light", "Thrown"}


@pytest.mark.asyncio
async def test_get_item_translated_resolves_armor_detail(db: AsyncSession) -> None:
    """get_item_translated resolves armor_detail for armor items."""
    await seed_catalog(db)
    results = await service.list_items_translated(db, search="Leather Armor")
    armor = await service.get_item_translated(db, results[0].id, locale="en")

    assert armor is not None
    assert armor.armor_detail is not None
    assert armor.armor_detail.base_ac == 11
    assert armor.equipment_category == "Light Armor"


@pytest.mark.asyncio
async def test_list_items_scoped_to_campaign_includes_srd_and_own_homebrew(
    db: AsyncSession,
) -> None:
    """`list_items(campaign_id=X)` returns SRD + own campaign homebrew, not others'."""
    await seed_catalog(db)
    srd_items = await service.list_items(db)
    equipment_category_id = srd_items[0].equipment_category_id

    campaign_a = uuid.uuid4()
    campaign_b = uuid.uuid4()
    homebrew_a = Item(
        id=uuid.uuid4(),
        index=None,
        item_type="gear",
        equipment_category_id=equipment_category_id,
        weight=1.0,
        cost=100,
        is_custom=True,
        campaign_id=campaign_a,
    )
    homebrew_b = Item(
        id=uuid.uuid4(),
        index=None,
        item_type="gear",
        equipment_category_id=equipment_category_id,
        weight=1.0,
        cost=100,
        is_custom=True,
        campaign_id=campaign_b,
    )
    db.add_all([homebrew_a, homebrew_b])
    await db.commit()

    results = await service.list_items(db, campaign_id=campaign_a)
    ids = {i.id for i in results}

    assert homebrew_a.id in ids
    assert homebrew_b.id not in ids
    assert {i.id for i in srd_items} <= ids


@pytest.mark.asyncio
async def test_get_item_not_found_returns_none(db: AsyncSession) -> None:
    """get_item should return None for an unknown ID."""
    result = await service.get_item(db, uuid.uuid4())
    assert result is None


@pytest.mark.asyncio
async def test_list_magic_items_returns_all(db: AsyncSession) -> None:
    """list_magic_items should return every seeded magic item, base + variants."""
    await seed_catalog(db)
    magic_items = await service.list_magic_items(db)
    assert len(magic_items) == 7


@pytest.mark.asyncio
async def test_get_magic_item_translated_resolves_variants(db: AsyncSession) -> None:
    """A base magic item (e.g. +1 Longsword) resolves its +2/+3 variants."""
    await seed_catalog(db)
    results = await service.list_magic_items_translated(db, search="+1 Longsword")
    plus_one = await service.get_magic_item_translated(db, results[0].id, locale="en")

    assert plus_one is not None
    assert plus_one.name == "+1 Longsword"
    assert plus_one.is_variant is False
    assert plus_one.variant_of_id is None
    variant_names = {v.name for v in plus_one.variants}
    assert variant_names == {"+2 Longsword", "+3 Longsword"}


@pytest.mark.asyncio
async def test_get_magic_item_translated_variant_points_back_to_base(
    db: AsyncSession,
) -> None:
    """A variant (e.g. +3 Longsword) carries `is_variant`/`variant_of_id`."""
    await seed_catalog(db)
    base_results = await service.list_magic_items_translated(db, search="+1 Longsword")
    base = base_results[0]
    variant_results = await service.list_magic_items_translated(
        db, search="+3 Longsword"
    )
    plus_three = await service.get_magic_item_translated(
        db, variant_results[0].id, locale="en"
    )

    assert plus_three is not None
    assert plus_three.is_variant is True
    assert plus_three.variant_of_id == base.id
    assert plus_three.rarity == "very_rare"


@pytest.mark.asyncio
async def test_get_magic_item_translated_falls_back_to_en(db: AsyncSession) -> None:
    """get_magic_item_translated falls back to `en` when locale has no translation."""
    await seed_catalog(db)
    results = await service.list_magic_items_translated(db, search="+1 Longsword")
    plus_one = await service.get_magic_item_translated(
        db, results[0].id, locale="pt-BR"
    )

    assert plus_one is not None
    assert plus_one.name == "+1 Longsword"


@pytest.mark.asyncio
async def test_list_magic_items_scoped_to_campaign_includes_srd_and_own_homebrew(
    db: AsyncSession,
) -> None:
    """`list_magic_items(campaign_id=X)` returns SRD + own homebrew, not others'."""
    await seed_catalog(db)
    srd_magic_items = await service.list_magic_items(db)
    equipment_category_id = srd_magic_items[0].equipment_category_id

    campaign_a = uuid.uuid4()
    campaign_b = uuid.uuid4()
    homebrew_a = MagicItem(
        id=uuid.uuid4(),
        index=None,
        equipment_category_id=equipment_category_id,
        rarity="rare",
        is_custom=True,
        campaign_id=campaign_a,
    )
    homebrew_b = MagicItem(
        id=uuid.uuid4(),
        index=None,
        equipment_category_id=equipment_category_id,
        rarity="rare",
        is_custom=True,
        campaign_id=campaign_b,
    )
    db.add_all([homebrew_a, homebrew_b])
    await db.commit()

    results = await service.list_magic_items(db, campaign_id=campaign_a)
    ids = {m.id for m in results}

    assert homebrew_a.id in ids
    assert homebrew_b.id not in ids
    assert {m.id for m in srd_magic_items} <= ids


@pytest.mark.asyncio
async def test_get_magic_item_not_found_returns_none(db: AsyncSession) -> None:
    """get_magic_item should return None for an unknown ID."""
    result = await service.get_magic_item(db, uuid.uuid4())
    assert result is None


@pytest.mark.asyncio
async def test_list_backgrounds_returns_all(db: AsyncSession) -> None:
    """list_backgrounds should return every seeded background."""
    await seed_catalog(db)
    backgrounds = await service.list_backgrounds(db)
    assert len(backgrounds) == 2


@pytest.mark.asyncio
async def test_get_background_translated_resolves_equipment_and_feature(
    db: AsyncSession,
) -> None:
    """get_background_translated resolves starting equipment and its feature."""
    await seed_catalog(db)
    results = await service.list_backgrounds_translated(db, search="Acolyte")
    acolyte = await service.get_background_translated(db, results[0].id, locale="en")

    assert acolyte is not None
    assert acolyte.name == "Acolyte"
    assert acolyte.feature is not None
    assert acolyte.feature.feature_name == "Shelter of the Faithful"
    assert any(e.item_name == "Backpack" for e in acolyte.equipment)


@pytest.mark.asyncio
async def test_get_background_translated_resolves_proficiencies(
    db: AsyncSession,
) -> None:
    """A background's granted proficiencies resolve via the junction table."""
    await seed_catalog(db)
    results = await service.list_backgrounds_translated(db, search="Acolyte")
    acolyte_id = results[0].id

    prof = Proficiency(
        id=uuid.uuid4(),
        index="thieves-tools",
        proficiency_type="other",
        is_custom=False,
    )
    db.add(prof)
    db.add(
        BackgroundProficiency(
            id=uuid.uuid4(), background_id=acolyte_id, proficiency_id=prof.id
        )
    )
    await db.commit()

    acolyte = await service.get_background_translated(db, acolyte_id, locale="en")
    assert acolyte is not None
    assert any(p.id == prof.id for p in acolyte.proficiencies)


@pytest.mark.asyncio
async def test_get_background_translated_falls_back_to_en(db: AsyncSession) -> None:
    """get_background_translated falls back to `en` when locale has no translation."""
    await seed_catalog(db)
    results = await service.list_backgrounds_translated(db, search="Acolyte")
    acolyte = await service.get_background_translated(
        db, results[0].id, locale="pt-BR"
    )

    assert acolyte is not None
    assert acolyte.name == "Acolyte"


@pytest.mark.asyncio
async def test_list_backgrounds_scoped_to_campaign_includes_srd_and_own_homebrew(
    db: AsyncSession,
) -> None:
    """`list_backgrounds(campaign_id=X)` returns SRD + own homebrew, not others'."""
    await seed_catalog(db)
    srd_backgrounds = await service.list_backgrounds(db)

    campaign_a = uuid.uuid4()
    campaign_b = uuid.uuid4()
    homebrew_a = Background(
        id=uuid.uuid4(), index=None, is_custom=True, campaign_id=campaign_a
    )
    homebrew_b = Background(
        id=uuid.uuid4(), index=None, is_custom=True, campaign_id=campaign_b
    )
    db.add_all([homebrew_a, homebrew_b])
    await db.commit()

    results = await service.list_backgrounds(db, campaign_id=campaign_a)
    ids = {b.id for b in results}

    assert homebrew_a.id in ids
    assert homebrew_b.id not in ids
    assert {b.id for b in srd_backgrounds} <= ids


@pytest.mark.asyncio
async def test_get_background_not_found_returns_none(db: AsyncSession) -> None:
    """get_background should return None for an unknown ID."""
    result = await service.get_background(db, uuid.uuid4())
    assert result is None


@pytest.mark.asyncio
async def test_list_feats_returns_all(db: AsyncSession) -> None:
    """list_feats should return every seeded feat."""
    await seed_catalog(db)
    feats = await service.list_feats(db)
    assert len(feats) == 3


@pytest.mark.asyncio
async def test_get_feat_translated_resolves_prerequisite(db: AsyncSession) -> None:
    """A feat's ability score prerequisite resolves via FeatPrerequisite."""
    await seed_catalog(db)
    results = await service.list_feats_translated(db, search="Grappler")
    grappler_id = results[0].id

    ability_score = AbilityScoreDefinition(
        id=uuid.uuid4(), index="str", is_custom=False
    )
    db.add(ability_score)
    db.add(
        FeatPrerequisite(
            id=uuid.uuid4(),
            feat_id=grappler_id,
            ability_score_id=ability_score.id,
            minimum_score=13,
        )
    )
    await db.commit()

    grappler = await service.get_feat_translated(db, grappler_id, locale="en")
    assert grappler is not None
    assert grappler.name == "Grappler"
    assert len(grappler.prerequisites) == 1
    assert grappler.prerequisites[0].ability_score_id == ability_score.id
    assert grappler.prerequisites[0].minimum_score == 13


@pytest.mark.asyncio
async def test_get_feat_translated_falls_back_to_en(db: AsyncSession) -> None:
    """get_feat_translated falls back to `en` when locale has no translation."""
    await seed_catalog(db)
    results = await service.list_feats_translated(db, search="Alert")
    alert = await service.get_feat_translated(db, results[0].id, locale="pt-BR")

    assert alert is not None
    assert alert.name == "Alert"


@pytest.mark.asyncio
async def test_list_feats_scoped_to_campaign_includes_srd_and_own_homebrew(
    db: AsyncSession,
) -> None:
    """`list_feats(campaign_id=X)` returns SRD + own campaign homebrew, not others'."""
    await seed_catalog(db)
    srd_feats = await service.list_feats(db)

    campaign_a = uuid.uuid4()
    campaign_b = uuid.uuid4()
    homebrew_a = Feat(
        id=uuid.uuid4(), index=None, is_custom=True, campaign_id=campaign_a
    )
    homebrew_b = Feat(
        id=uuid.uuid4(), index=None, is_custom=True, campaign_id=campaign_b
    )
    db.add_all([homebrew_a, homebrew_b])
    await db.commit()

    results = await service.list_feats(db, campaign_id=campaign_a)
    ids = {f.id for f in results}

    assert homebrew_a.id in ids
    assert homebrew_b.id not in ids
    assert {f.id for f in srd_feats} <= ids


@pytest.mark.asyncio
async def test_get_feat_not_found_returns_none(db: AsyncSession) -> None:
    """get_feat should return None for an unknown ID."""
    result = await service.get_feat(db, uuid.uuid4())
    assert result is None
