"""Tests for the catalog seed function."""

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.catalog import service
from app.catalog.models import (
    AbilityScoreDefinition,
    Alignment,
    Background,
    ClassDefinition,
    Condition,
    DamageType,
    EquipmentCategory,
    Feat,
    Feature,
    Item,
    Language,
    MagicItem,
    MagicSchool,
    Monster,
    Proficiency,
    Race,
    Rule,
    RuleSection,
    SkillDefinition,
    Spell,
    WeaponProperty,
)
from app.catalog.seeds.seed import (
    backfill_feature_parent_ids,
    backfill_spell_action_target_types,
    seed_catalog,
)

#: Row counts for the full SRD 2014 `en` seed — see PRD §7.4.1-7.4.9. These
#: are the real published SRD sizes (not a subset), so any change here should
#: be backed by a change to `_data/2014/en/*.json` or `convert_srd.py`, not a
#: shortcut to make a test pass.
_EXPECTED_COUNTS = {
    AbilityScoreDefinition: 6,
    SkillDefinition: 18,
    Alignment: 9,
    Condition: 15,
    DamageType: 13,
    MagicSchool: 8,
    Language: 16,
    WeaponProperty: 11,
    EquipmentCategory: 39,
    Proficiency: 117,
    Race: 9,
    ClassDefinition: 12,
    Spell: 319,
    Item: 237,
    MagicItem: 362,
    Background: 1,
    Feat: 1,
    Monster: 334,
    RuleSection: 6,
    Rule: 33,
}


@pytest.mark.asyncio
async def test_seed_populates_every_category_with_srd_counts(db: AsyncSession) -> None:
    """seed_catalog should insert the full SRD 2014 `en` row count per table."""
    await seed_catalog(db)

    for model, expected in _EXPECTED_COUNTS.items():
        count = await db.scalar(select(func.count()).select_from(model))
        assert count == expected, f"{model.__name__}: expected {expected}, got {count}"


@pytest.mark.asyncio
async def test_seed_creates_races(db: AsyncSession) -> None:
    """seed_catalog should insert all 9 SRD races, translated."""
    await seed_catalog(db)

    races = (await db.execute(select(Race).order_by(Race.index))).scalars().all()
    indexes = {r.index for r in races}
    assert indexes == {
        "dragonborn",
        "dwarf",
        "elf",
        "gnome",
        "half-elf",
        "half-orc",
        "halfling",
        "human",
        "tiefling",
    }

    summaries = await service.list_races_translated(db)
    names = {r.name for r in summaries}
    assert "Human" in names
    assert "Elf" in names


@pytest.mark.asyncio
async def test_seed_creates_classes(db: AsyncSession) -> None:
    """seed_catalog should insert all 12 SRD classes."""
    await seed_catalog(db)

    classes = (
        (await db.execute(select(ClassDefinition).order_by(ClassDefinition.index)))
        .scalars()
        .all()
    )
    indexes = {c.index for c in classes}
    assert indexes == {
        "barbarian",
        "bard",
        "cleric",
        "druid",
        "fighter",
        "monk",
        "paladin",
        "ranger",
        "rogue",
        "sorcerer",
        "warlock",
        "wizard",
    }

    summaries = await service.list_classes_translated(db)
    names = {c.name for c in summaries}
    assert "Fighter" in names
    assert "Wizard" in names


@pytest.mark.asyncio
async def test_seed_creates_spells(db: AsyncSession) -> None:
    """seed_catalog should insert the 319 SRD spells."""
    await seed_catalog(db)

    spells = (await db.execute(select(Spell))).scalars().all()
    assert len(spells) == 319


async def test_seed_classifies_spell_action_and_target_type(db: AsyncSession) -> None:
    """Attack/save/no-roll spells are classified from the SRD's own structure."""
    await seed_catalog(db)

    fire_bolt = (
        await db.execute(select(Spell).where(Spell.index == "fire-bolt"))
    ).scalar_one()
    fireball = (
        await db.execute(select(Spell).where(Spell.index == "fireball"))
    ).scalar_one()
    mage_armor = (
        await db.execute(select(Spell).where(Spell.index == "mage-armor"))
    ).scalar_one()

    assert fire_bolt.action_type == "attack_roll"
    assert fire_bolt.target_type == "enemy"

    assert fireball.action_type == "saving_throw"
    assert fireball.target_type == "area"
    assert fireball.save_ability_score_id is not None
    dex = (
        await db.execute(
            select(AbilityScoreDefinition).where(AbilityScoreDefinition.index == "dex")
        )
    ).scalar_one()
    assert fireball.save_ability_score_id == dex.id

    assert mage_armor.action_type == "cast_only"
    assert mage_armor.save_ability_score_id is None


async def test_backfill_spell_action_target_types_is_idempotent_and_preserves_ids(
    db: AsyncSession,
) -> None:
    """Running the backfill again doesn't change ids or duplicate rows."""
    await seed_catalog(db)
    before = (
        await db.execute(
            select(Spell.id, Spell.action_type).where(Spell.index == "fireball")
        )
    ).one()

    await backfill_spell_action_target_types(db)
    await db.commit()

    after = (
        await db.execute(
            select(Spell.id, Spell.action_type).where(Spell.index == "fireball")
        )
    ).one()
    assert after == before


@pytest.mark.asyncio
async def test_seed_creates_items(db: AsyncSession) -> None:
    """seed_catalog should insert the 237 SRD equipment items."""
    await seed_catalog(db)

    items = (await db.execute(select(Item))).scalars().all()
    assert len(items) == 237


@pytest.mark.asyncio
async def test_seed_creates_magic_items_with_variants(db: AsyncSession) -> None:
    """seed_catalog should insert the 362 SRD magic items, base + variants."""
    await seed_catalog(db)

    magic_items = (await db.execute(select(MagicItem))).scalars().all()
    assert len(magic_items) == 362
    assert any(mi.is_variant for mi in magic_items)
    assert any(not mi.is_variant for mi in magic_items)


@pytest.mark.asyncio
async def test_seed_creates_backgrounds(db: AsyncSession) -> None:
    """seed_catalog should insert the 1 SRD background (Acolyte)."""
    await seed_catalog(db)

    backgrounds = (
        (await db.execute(select(Background).order_by(Background.index)))
        .scalars()
        .all()
    )
    indexes = {b.index for b in backgrounds}
    assert indexes == {"acolyte"}

    summaries = await service.list_backgrounds_translated(db)
    names = {b.name for b in summaries}
    assert names == {"Acolyte"}


@pytest.mark.asyncio
async def test_seed_creates_feats(db: AsyncSession) -> None:
    """seed_catalog should insert the 1 SRD feat (Grappler)."""
    await seed_catalog(db)

    feats = (await db.execute(select(Feat).order_by(Feat.index))).scalars().all()
    indexes = {f.index for f in feats}
    assert indexes == {"grappler"}


@pytest.mark.asyncio
async def test_seed_creates_monsters(db: AsyncSession) -> None:
    """seed_catalog should insert all 334 SRD monsters."""
    await seed_catalog(db)

    monsters = (
        (await db.execute(select(Monster).order_by(Monster.index))).scalars().all()
    )
    assert len(monsters) == 334
    indexes = {m.index for m in monsters}
    assert "goblin" in indexes
    assert "adult-red-dragon" in indexes

    summaries = await service.list_monsters_translated(db, search="Goblin")
    names = {m.name for m in summaries}
    assert "Goblin" in names


@pytest.mark.asyncio
async def test_seed_creates_rules(db: AsyncSession) -> None:
    """seed_catalog should insert the 33 rules across 6 rule sections."""
    await seed_catalog(db)

    rules = (await db.execute(select(Rule).order_by(Rule.index))).scalars().all()
    assert len(rules) == 33
    sections = (
        (await db.execute(select(RuleSection).order_by(RuleSection.index)))
        .scalars()
        .all()
    )
    assert {s.index for s in sections} == {
        "adventuring",
        "appendix",
        "combat",
        "equipment",
        "spellcasting",
        "using-ability-scores",
    }


@pytest.mark.asyncio
async def test_seed_is_idempotent(db: AsyncSession) -> None:
    """Running seed_catalog twice should not duplicate rows in any category."""
    await seed_catalog(db)
    await seed_catalog(db)

    for model, expected in _EXPECTED_COUNTS.items():
        count = await db.scalar(select(func.count()).select_from(model))
        assert count == expected, f"{model.__name__}: expected {expected}, got {count}"


async def test_seed_links_fighting_style_options_to_parent_feature(
    db: AsyncSession,
) -> None:
    """A named option (e.g. Fighting Style: Archery) links to its parent feature."""
    await seed_catalog(db)

    parent = (
        await db.execute(
            select(Feature).where(Feature.index == "ranger-fighting-style")
        )
    ).scalar_one()
    option = (
        await db.execute(
            select(Feature).where(Feature.index == "ranger-fighting-style-archery")
        )
    ).scalar_one()

    assert option.parent_feature_id == parent.id


async def test_backfill_feature_parent_ids_is_idempotent_and_preserves_ids(
    db: AsyncSession,
) -> None:
    """Running the backfill again doesn't change ids or duplicate rows."""
    await seed_catalog(db)
    before = (
        await db.execute(
            select(Feature.id, Feature.parent_feature_id).where(
                Feature.index == "ranger-fighting-style-archery"
            )
        )
    ).one()

    await backfill_feature_parent_ids(db)
    await db.commit()

    after = (
        await db.execute(
            select(Feature.id, Feature.parent_feature_id).where(
                Feature.index == "ranger-fighting-style-archery"
            )
        )
    ).one()
    assert after == before
