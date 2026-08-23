"""Tests covering creation + translated read for the 8 fixed-vocabulary entities."""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.catalog import service
from app.catalog.domain import LanguageType
from app.catalog.models import (
    AbilityScoreDefinition,
    AbilityScoreDefinitionI18n,
    Alignment,
    AlignmentI18n,
    Condition,
    ConditionI18n,
    DamageType,
    DamageTypeI18n,
    Language,
    LanguageI18n,
    MagicSchool,
    MagicSchoolI18n,
    SkillDefinition,
    SkillDefinitionI18n,
    WeaponProperty,
    WeaponPropertyI18n,
)


@pytest.mark.asyncio
async def test_ability_score_definition_create_and_translated_read(
    db: AsyncSession,
) -> None:
    """AbilityScoreDefinition can be created and read back translated."""
    entity = AbilityScoreDefinition(id=uuid.uuid4(), index="str", is_custom=False)
    db.add(entity)
    db.add(
        AbilityScoreDefinitionI18n(
            id=uuid.uuid4(),
            entity_id=entity.id,
            locale="en",
            name="STR",
            full_name="Strength",
            desc="Measures bodily power.",
        )
    )
    await db.commit()

    fetched = await service.get_ability_score(db, entity.id)
    assert fetched is not None
    assert fetched.index == "str"

    translated = await service.get_translated(
        db,
        AbilityScoreDefinitionI18n,
        AbilityScoreDefinitionI18n.entity_id,
        entity_id=entity.id,
        locale="en",
    )
    assert translated is not None
    assert translated.full_name == "Strength"

    all_scores = await service.list_ability_scores(db)
    assert len(all_scores) == 1


@pytest.mark.asyncio
async def test_skill_definition_create_and_translated_read(db: AsyncSession) -> None:
    """SkillDefinition references an AbilityScoreDefinition and reads translated."""
    ability = AbilityScoreDefinition(id=uuid.uuid4(), index="dex", is_custom=False)
    db.add(ability)
    skill = SkillDefinition(
        id=uuid.uuid4(), index="stealth", ability_score_id=ability.id, is_custom=False
    )
    db.add(skill)
    db.add(
        SkillDefinitionI18n(
            id=uuid.uuid4(),
            entity_id=skill.id,
            locale="en",
            name="Stealth",
            desc="Hide from view.",
        )
    )
    await db.commit()

    fetched = await service.get_skill(db, skill.id)
    assert fetched is not None
    assert fetched.ability_score_id == ability.id

    translated = await service.get_translated(
        db,
        SkillDefinitionI18n,
        SkillDefinitionI18n.entity_id,
        entity_id=skill.id,
        locale="en",
    )
    assert translated is not None
    assert translated.name == "Stealth"


@pytest.mark.asyncio
async def test_alignment_create_and_translated_read(db: AsyncSession) -> None:
    """Alignment can be created and read back translated."""
    entity = Alignment(id=uuid.uuid4(), index="lawful-good", is_custom=False)
    db.add(entity)
    db.add(
        AlignmentI18n(
            id=uuid.uuid4(),
            entity_id=entity.id,
            locale="en",
            name="Lawful Good",
            abbreviation="LG",
            desc="Acts with compassion and honor.",
        )
    )
    await db.commit()

    fetched = await service.get_alignment(db, entity.id)
    assert fetched is not None

    translated = await service.get_translated(
        db, AlignmentI18n, AlignmentI18n.entity_id, entity_id=entity.id, locale="en"
    )
    assert translated is not None
    assert translated.abbreviation == "LG"


@pytest.mark.asyncio
async def test_condition_create_and_translated_read(db: AsyncSession) -> None:
    """Condition can be created and read back translated."""
    entity = Condition(id=uuid.uuid4(), index="poisoned", is_custom=False)
    db.add(entity)
    db.add(
        ConditionI18n(
            id=uuid.uuid4(),
            entity_id=entity.id,
            locale="en",
            name="Poisoned",
            desc="Disadvantage on attack rolls and ability checks.",
        )
    )
    await db.commit()

    fetched = await service.get_condition(db, entity.id)
    assert fetched is not None

    translated = await service.get_translated(
        db, ConditionI18n, ConditionI18n.entity_id, entity_id=entity.id, locale="en"
    )
    assert translated is not None
    assert translated.name == "Poisoned"


@pytest.mark.asyncio
async def test_damage_type_create_and_translated_read(db: AsyncSession) -> None:
    """DamageType can be created and read back translated."""
    entity = DamageType(id=uuid.uuid4(), index="fire", is_custom=False)
    db.add(entity)
    db.add(
        DamageTypeI18n(
            id=uuid.uuid4(),
            entity_id=entity.id,
            locale="en",
            name="Fire",
            desc="Fire damage.",
        )
    )
    await db.commit()

    fetched = await service.get_damage_type(db, entity.id)
    assert fetched is not None

    translated = await service.get_translated(
        db, DamageTypeI18n, DamageTypeI18n.entity_id, entity_id=entity.id, locale="en"
    )
    assert translated is not None
    assert translated.name == "Fire"


@pytest.mark.asyncio
async def test_magic_school_create_and_translated_read(db: AsyncSession) -> None:
    """MagicSchool can be created and read back translated, with nullable desc."""
    entity = MagicSchool(id=uuid.uuid4(), index="evocation", is_custom=False)
    db.add(entity)
    db.add(
        MagicSchoolI18n(
            id=uuid.uuid4(),
            entity_id=entity.id,
            locale="en",
            name="Evocation",
            desc=None,
        )
    )
    await db.commit()

    fetched = await service.get_magic_school(db, entity.id)
    assert fetched is not None

    translated = await service.get_translated(
        db, MagicSchoolI18n, MagicSchoolI18n.entity_id, entity_id=entity.id, locale="en"
    )
    assert translated is not None
    assert translated.name == "Evocation"
    assert translated.desc is None


@pytest.mark.asyncio
async def test_language_create_and_translated_read(db: AsyncSession) -> None:
    """Language stores a structural `language_type` and reads translated."""
    entity = Language(
        id=uuid.uuid4(),
        index="common",
        language_type=LanguageType.standard,
        is_custom=False,
    )
    db.add(entity)
    db.add(
        LanguageI18n(
            id=uuid.uuid4(),
            entity_id=entity.id,
            locale="en",
            name="Common",
            desc="The trade language.",
            script="Common",
            typical_speakers="Humans",
        )
    )
    await db.commit()

    fetched = await service.get_language(db, entity.id)
    assert fetched is not None
    assert fetched.language_type == LanguageType.standard

    translated = await service.get_translated(
        db, LanguageI18n, LanguageI18n.entity_id, entity_id=entity.id, locale="en"
    )
    assert translated is not None
    assert translated.script == "Common"


@pytest.mark.asyncio
async def test_weapon_property_create_and_translated_read(db: AsyncSession) -> None:
    """WeaponProperty can be created and read back translated."""
    entity = WeaponProperty(id=uuid.uuid4(), index="finesse", is_custom=False)
    db.add(entity)
    db.add(
        WeaponPropertyI18n(
            id=uuid.uuid4(),
            entity_id=entity.id,
            locale="en",
            name="Finesse",
            desc="Use Dex instead of Str.",
        )
    )
    await db.commit()

    fetched = await service.get_weapon_property(db, entity.id)
    assert fetched is not None

    translated = await service.get_translated(
        db,
        WeaponPropertyI18n,
        WeaponPropertyI18n.entity_id,
        entity_id=entity.id,
        locale="en",
    )
    assert translated is not None
    assert translated.name == "Finesse"

    all_props = await service.list_weapon_properties(db)
    assert len(all_props) == 1
