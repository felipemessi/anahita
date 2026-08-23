"""Tests for the Proficiency catalog entity and its reference-scope invariant."""

import uuid

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.catalog import service
from app.catalog.domain import (
    ProficiencyReferenceScopeError,
    ProficiencyType,
    validate_proficiency_reference_scope,
)
from app.catalog.models import (
    AbilityScoreDefinition,
    ClassDefinition,
    Proficiency,
    ProficiencyClass,
    ProficiencyI18n,
    ProficiencyRace,
    Race,
    SkillDefinition,
)


def test_validate_accepts_skill_type_with_skill_id() -> None:
    """`proficiency_type=skill` requires only `skill_id` set."""
    validate_proficiency_reference_scope(
        proficiency_type=ProficiencyType.skill,
        skill_id=uuid.uuid4(),
        ability_score_id=None,
        equipment_category_id=None,
    )


def test_validate_accepts_saving_throw_with_ability_score_id() -> None:
    """`proficiency_type=saving_throw` requires only `ability_score_id` set."""
    validate_proficiency_reference_scope(
        proficiency_type=ProficiencyType.saving_throw,
        skill_id=None,
        ability_score_id=uuid.uuid4(),
        equipment_category_id=None,
    )


@pytest.mark.parametrize(
    "proficiency_type",
    [ProficiencyType.weapon, ProficiencyType.armor, ProficiencyType.tool],
)
def test_validate_accepts_equipment_types_with_equipment_category_id(
    proficiency_type: ProficiencyType,
) -> None:
    """`weapon`/`armor`/`tool` require only `equipment_category_id` set."""
    validate_proficiency_reference_scope(
        proficiency_type=proficiency_type,
        skill_id=None,
        ability_score_id=None,
        equipment_category_id=uuid.uuid4(),
    )


def test_validate_accepts_other_with_no_references() -> None:
    """`proficiency_type=other` requires no reference FK set."""
    validate_proficiency_reference_scope(
        proficiency_type=ProficiencyType.other,
        skill_id=None,
        ability_score_id=None,
        equipment_category_id=None,
    )


def test_validate_rejects_skill_type_missing_skill_id() -> None:
    """`proficiency_type=skill` without `skill_id` is invalid."""
    with pytest.raises(ProficiencyReferenceScopeError):
        validate_proficiency_reference_scope(
            proficiency_type=ProficiencyType.skill,
            skill_id=None,
            ability_score_id=None,
            equipment_category_id=None,
        )


def test_validate_rejects_skill_type_with_extra_reference() -> None:
    """`proficiency_type=skill` must not also set `ability_score_id`."""
    with pytest.raises(ProficiencyReferenceScopeError):
        validate_proficiency_reference_scope(
            proficiency_type=ProficiencyType.skill,
            skill_id=uuid.uuid4(),
            ability_score_id=uuid.uuid4(),
            equipment_category_id=None,
        )


def test_validate_rejects_other_with_a_reference_set() -> None:
    """`proficiency_type=other` must not set any reference FK."""
    with pytest.raises(ProficiencyReferenceScopeError):
        validate_proficiency_reference_scope(
            proficiency_type=ProficiencyType.other,
            skill_id=uuid.uuid4(),
            ability_score_id=None,
            equipment_category_id=None,
        )


@pytest.mark.asyncio
async def test_db_check_constraint_rejects_mismatched_reference(
    db: AsyncSession,
) -> None:
    """The CHECK constraint mirrors the Python-level invariant at the DB level."""
    db.add(
        Proficiency(
            id=uuid.uuid4(),
            index="broken",
            proficiency_type=ProficiencyType.other,
            skill_id=uuid.uuid4(),
            is_custom=False,
        )
    )
    with pytest.raises(IntegrityError):
        await db.commit()


@pytest.mark.asyncio
async def test_proficiency_create_and_translated_read(db: AsyncSession) -> None:
    """Proficiency can be created, read back, and translated."""
    ability = AbilityScoreDefinition(id=uuid.uuid4(), index="dex", is_custom=False)
    db.add(ability)
    skill = SkillDefinition(
        id=uuid.uuid4(), index="stealth", ability_score_id=ability.id, is_custom=False
    )
    db.add(skill)
    prof = Proficiency(
        id=uuid.uuid4(),
        index="skill-stealth",
        proficiency_type=ProficiencyType.skill,
        skill_id=skill.id,
        is_custom=False,
    )
    db.add(prof)
    db.add(
        ProficiencyI18n(
            id=uuid.uuid4(), entity_id=prof.id, locale="en", name="Skill: Stealth"
        )
    )
    await db.commit()

    fetched = await service.get_proficiency(db, prof.id)
    assert fetched is not None
    assert fetched.skill_id == skill.id

    translated = await service.get_translated(
        db, ProficiencyI18n, ProficiencyI18n.entity_id, entity_id=prof.id, locale="en"
    )
    assert translated is not None
    assert translated.name == "Skill: Stealth"

    all_profs = await service.list_proficiencies(db)
    assert len(all_profs) == 1


@pytest.mark.asyncio
async def test_list_proficiencies_for_class_and_race(db: AsyncSession) -> None:
    """Junction tables link a Proficiency to the classes/races that grant it."""
    prof = Proficiency(
        id=uuid.uuid4(),
        index="tool-thieves",
        proficiency_type=ProficiencyType.other,
        is_custom=False,
    )
    db.add(prof)
    cls = ClassDefinition(
        id=uuid.uuid4(),
        index="rogue",
        hit_die=8,
        primary_ability="dex",
        saving_throw_proficiencies="dex,int",
        is_custom=False,
    )
    db.add(cls)
    race = Race(id=uuid.uuid4(), index="human", speed=30, is_custom=False)
    db.add(race)
    db.add(
        ProficiencyClass(
            id=uuid.uuid4(), proficiency_id=prof.id, class_definition_id=cls.id
        )
    )
    db.add(ProficiencyRace(id=uuid.uuid4(), proficiency_id=prof.id, race_id=race.id))
    await db.commit()

    for_class = await service.list_proficiencies_for_class(db, cls.id)
    for_race = await service.list_proficiencies_for_race(db, race.id)

    assert [p.id for p in for_class] == [prof.id]
    assert [p.id for p in for_race] == [prof.id]
