"""Tests for skill proficiency choices (Fase 10).

`ProficiencyChoiceGroup`/`ProficiencyChoiceOption` aren't populated by
`seed_catalog` yet (same documented gap as `BackgroundProficiency`/
`FeatPrerequisite` in Fase 7) — every test builds the catalog rows it needs
directly, same precedent as `tests/catalog/test_proficiencies.py`.
"""

import uuid

import pytest
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.campaigns.domain import CampaignRole
from app.campaigns.models import Campaign, CampaignMember
from app.catalog.domain import AbilityScore, ProficiencyType
from app.catalog.models import (
    Proficiency,
    ProficiencyChoiceGroup,
    ProficiencyChoiceOption,
    ProficiencyClass,
    SkillDefinition,
)
from app.characters.domain import Skill
from app.characters.schemas import (
    CharacterAbilityScoreCreate,
    CharacterClassCreate,
    CharacterCreate,
    CharacterProficiencyChoiceRequest,
)
from app.characters.service import CharacterService

_STANDARD_ARRAY = {
    AbilityScore.str: 15,
    AbilityScore.dex: 14,
    AbilityScore.con: 13,
    AbilityScore.int: 12,
    AbilityScore.wis: 10,
    AbilityScore.cha: 8,
}


def _ability_scores() -> list[CharacterAbilityScoreCreate]:
    return [
        CharacterAbilityScoreCreate(ability=ability, base_score=score)
        for ability, score in _STANDARD_ARRAY.items()
    ]


async def _make_user(db: AsyncSession, *, email: str) -> User:
    user = User(email=email, username=email.split("@")[0], hashed_password="x")
    db.add(user)
    await db.flush()
    return user


async def _make_membership(db: AsyncSession, owner: User) -> CampaignMember:
    campaign = Campaign(name="Test Table", owner_id=owner.id)
    db.add(campaign)
    await db.flush()
    member = CampaignMember(
        campaign_id=campaign.id, user_id=owner.id, role=CampaignRole.dm
    )
    db.add(member)
    await db.commit()
    await db.refresh(member)
    return member


async def _skill_proficiency(db: AsyncSession, skill: Skill) -> Proficiency:
    """Return (creating if needed) the skill `Proficiency` row for `skill`."""
    index = skill.value.replace("_", "-")
    skill_def = (
        await db.execute(select(SkillDefinition).where(SkillDefinition.index == index))
    ).scalar_one()
    prof = Proficiency(
        id=uuid.uuid4(),
        index=f"skill-{index}",
        proficiency_type=ProficiencyType.skill,
        skill_id=skill_def.id,
        is_custom=False,
    )
    db.add(prof)
    await db.flush()
    return prof


async def _create_character(
    db: AsyncSession,
    *,
    owner: User,
    member: CampaignMember,
    race_id: str,
    class_id: str,
) -> uuid.UUID:
    service = CharacterService()
    character = await service.create_character(
        owner.id,
        CharacterCreate(
            campaign_member_id=member.id,
            name="Test Character",
            race_id=uuid.UUID(race_id),
            ability_scores=_ability_scores(),
            classes=[CharacterClassCreate(class_definition_id=uuid.UUID(class_id))],
        ),
        db,
    )
    return character.id


async def test_fixed_skill_proficiency_applied_automatically(
    db: AsyncSession, human_race_id: str, fighter_class_id: str
) -> None:
    """A skill the class grants with no choice is proficient right at creation."""
    athletics = await _skill_proficiency(db, Skill.athletics)
    db.add(
        ProficiencyClass(
            id=uuid.uuid4(),
            proficiency_id=athletics.id,
            class_definition_id=uuid.UUID(fighter_class_id),
        )
    )
    await db.commit()

    owner = await _make_user(db, email="fixed@example.com")
    member = await _make_membership(db, owner)
    character_id = await _create_character(
        db, owner=owner, member=member, race_id=human_race_id, class_id=fighter_class_id
    )

    service = CharacterService()
    character = await service.get_character(character_id, owner.id, db)
    skills_by_name = {s.skill: s for s in character.skills}
    assert skills_by_name[Skill.athletics].proficient is True
    # Every other skill stays untouched (no choice made, no other fixed grant).
    assert skills_by_name[Skill.stealth].proficient is False


async def test_race_choice_within_valid_set_accepted(
    db: AsyncSession, human_race_id: str, fighter_class_id: str
) -> None:
    """Picking a skill inside the race's "choose N of [...]" set is accepted."""
    insight = await _skill_proficiency(db, Skill.insight)
    perception = await _skill_proficiency(db, Skill.perception)
    survival = await _skill_proficiency(db, Skill.survival)
    group = ProficiencyChoiceGroup(
        id=uuid.uuid4(), race_id=uuid.UUID(human_race_id), choose_count=1
    )
    db.add(group)
    await db.flush()
    for prof in (insight, perception, survival):
        db.add(
            ProficiencyChoiceOption(
                id=uuid.uuid4(), group_id=group.id, proficiency_id=prof.id
            )
        )
    await db.commit()

    owner = await _make_user(db, email="choice@example.com")
    member = await _make_membership(db, owner)
    character_id = await _create_character(
        db, owner=owner, member=member, race_id=human_race_id, class_id=fighter_class_id
    )

    service = CharacterService()
    character = await service.set_proficiency_choices(
        character_id,
        owner.id,
        CharacterProficiencyChoiceRequest(skills=[Skill.perception]),
        db,
    )

    skills_by_name = {s.skill: s for s in character.skills}
    assert skills_by_name[Skill.perception].proficient is True
    assert skills_by_name[Skill.insight].proficient is False


async def test_choice_outside_valid_set_rejected(
    db: AsyncSession, human_race_id: str, fighter_class_id: str
) -> None:
    """Picking a skill outside every valid choice group is a 422."""
    insight = await _skill_proficiency(db, Skill.insight)
    group = ProficiencyChoiceGroup(
        id=uuid.uuid4(), race_id=uuid.UUID(human_race_id), choose_count=1
    )
    db.add(group)
    await db.flush()
    db.add(
        ProficiencyChoiceOption(
            id=uuid.uuid4(), group_id=group.id, proficiency_id=insight.id
        )
    )
    await db.commit()

    owner = await _make_user(db, email="rejected@example.com")
    member = await _make_membership(db, owner)
    character_id = await _create_character(
        db, owner=owner, member=member, race_id=human_race_id, class_id=fighter_class_id
    )

    service = CharacterService()
    with pytest.raises(HTTPException) as exc_info:
        await service.set_proficiency_choices(
            character_id,
            owner.id,
            CharacterProficiencyChoiceRequest(skills=[Skill.stealth]),
            db,
        )
    assert exc_info.value.status_code == 422


async def test_choice_exceeding_choose_count_rejected(
    db: AsyncSession, human_race_id: str, fighter_class_id: str
) -> None:
    """Picking more skills from one group than its `choose_count` is a 422."""
    insight = await _skill_proficiency(db, Skill.insight)
    perception = await _skill_proficiency(db, Skill.perception)
    group = ProficiencyChoiceGroup(
        id=uuid.uuid4(), race_id=uuid.UUID(human_race_id), choose_count=1
    )
    db.add(group)
    await db.flush()
    for prof in (insight, perception):
        db.add(
            ProficiencyChoiceOption(
                id=uuid.uuid4(), group_id=group.id, proficiency_id=prof.id
            )
        )
    await db.commit()

    owner = await _make_user(db, email="toomany@example.com")
    member = await _make_membership(db, owner)
    character_id = await _create_character(
        db, owner=owner, member=member, race_id=human_race_id, class_id=fighter_class_id
    )

    service = CharacterService()
    with pytest.raises(HTTPException) as exc_info:
        await service.set_proficiency_choices(
            character_id,
            owner.id,
            CharacterProficiencyChoiceRequest(
                skills=[Skill.insight, Skill.perception]
            ),
            db,
        )
    assert exc_info.value.status_code == 422


async def test_choice_wrong_owner_rejected(
    db: AsyncSession, human_race_id: str, fighter_class_id: str
) -> None:
    """A player who doesn't own the character can't set its proficiencies."""
    insight = await _skill_proficiency(db, Skill.insight)
    group = ProficiencyChoiceGroup(
        id=uuid.uuid4(), race_id=uuid.UUID(human_race_id), choose_count=1
    )
    db.add(group)
    await db.flush()
    db.add(
        ProficiencyChoiceOption(
            id=uuid.uuid4(), group_id=group.id, proficiency_id=insight.id
        )
    )
    await db.commit()

    owner = await _make_user(db, email="owner@example.com")
    member = await _make_membership(db, owner)
    character_id = await _create_character(
        db, owner=owner, member=member, race_id=human_race_id, class_id=fighter_class_id
    )
    intruder = await _make_user(db, email="intruder@example.com")

    service = CharacterService()
    with pytest.raises(HTTPException) as exc_info:
        await service.set_proficiency_choices(
            character_id,
            intruder.id,
            CharacterProficiencyChoiceRequest(skills=[Skill.insight]),
            db,
        )
    assert exc_info.value.status_code == 403


async def test_class_choice_and_race_choice_are_both_honored(
    db: AsyncSession, human_race_id: str, fighter_class_id: str
) -> None:
    """A skill valid only through the class's group (not the race's) is accepted."""
    arcana = await _skill_proficiency(db, Skill.arcana)
    class_group = ProficiencyChoiceGroup(
        id=uuid.uuid4(),
        class_definition_id=uuid.UUID(fighter_class_id),
        choose_count=2,
    )
    db.add(class_group)
    await db.flush()
    db.add(
        ProficiencyChoiceOption(
            id=uuid.uuid4(), group_id=class_group.id, proficiency_id=arcana.id
        )
    )
    await db.commit()

    owner = await _make_user(db, email="classchoice@example.com")
    member = await _make_membership(db, owner)
    character_id = await _create_character(
        db, owner=owner, member=member, race_id=human_race_id, class_id=fighter_class_id
    )

    service = CharacterService()
    character = await service.set_proficiency_choices(
        character_id,
        owner.id,
        CharacterProficiencyChoiceRequest(skills=[Skill.arcana]),
        db,
    )
    skills_by_name = {s.skill: s for s in character.skills}
    assert skills_by_name[Skill.arcana].proficient is True
