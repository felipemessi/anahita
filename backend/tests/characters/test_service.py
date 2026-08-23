"""Integration tests for CharacterService using SQLite in-memory database."""

import uuid

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.campaigns.domain import CampaignRole
from app.campaigns.models import Campaign, CampaignMember
from app.catalog.domain import AbilityScore
from app.catalog.models import Race
from app.characters.schemas import (
    CharacterAbilityScoreCreate,
    CharacterClassCreate,
    CharacterCreate,
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


async def test_create_character_simple_race_and_class(
    db: AsyncSession, human_race_id: str, fighter_class_id: str
) -> None:
    """A level-1 human fighter can be created with a standard ability array."""
    owner = await _make_user(db, email="player@example.com")
    member = await _make_membership(db, owner)
    service = CharacterService()

    character = await service.create_character(
        owner.id,
        CharacterCreate(
            campaign_member_id=member.id,
            name="Aldric",
            race_id=uuid.UUID(human_race_id),
            ability_scores=_ability_scores(),
            classes=[
                CharacterClassCreate(class_definition_id=uuid.UUID(fighter_class_id))
            ],
        ),
        db,
    )

    assert character.name == "Aldric"
    assert character.campaign_member_id == member.id
    assert len(character.ability_scores) == 6
    assert len(character.classes) == 1
    assert character.classes[0].class_definition_id == uuid.UUID(fighter_class_id)
    # Fighter hit die is d10; CON 13 -> +1 modifier; level 1.
    assert character.hit_point_max == 11
    assert character.hit_point_current == 11
    assert character.proficiency_bonus == 2


async def test_create_character_for_someone_elses_membership_rejected(
    db: AsyncSession, human_race_id: str, fighter_class_id: str
) -> None:
    """A user cannot create a character for a membership they don't own."""
    owner = await _make_user(db, email="owner@example.com")
    outsider = await _make_user(db, email="outsider@example.com")
    member = await _make_membership(db, owner)
    service = CharacterService()

    with pytest.raises(HTTPException) as exc:
        await service.create_character(
            outsider.id,
            CharacterCreate(
                campaign_member_id=member.id,
                name="Intruder",
                race_id=uuid.UUID(human_race_id),
                ability_scores=_ability_scores(),
                classes=[
                    CharacterClassCreate(class_definition_id=uuid.UUID(fighter_class_id))
                ],
            ),
            db,
        )
    assert exc.value.status_code == 403


async def test_create_character_rejects_custom_race_from_another_campaign(
    db: AsyncSession, fighter_class_id: str
) -> None:
    """A character cannot reference homebrew race content from another campaign."""
    owner = await _make_user(db, email="player@example.com")
    member = await _make_membership(db, owner)

    other_campaign = Campaign(name="Other Table", owner_id=owner.id)
    db.add(other_campaign)
    await db.flush()
    homebrew_race = Race(
        speed=30, size="medium", is_custom=True, campaign_id=other_campaign.id
    )
    db.add(homebrew_race)
    await db.commit()
    await db.refresh(homebrew_race)

    service = CharacterService()
    with pytest.raises(HTTPException) as exc:
        await service.create_character(
            owner.id,
            CharacterCreate(
                campaign_member_id=member.id,
                name="Leaky Homebrew",
                race_id=homebrew_race.id,
                ability_scores=_ability_scores(),
                classes=[
                    CharacterClassCreate(class_definition_id=uuid.UUID(fighter_class_id))
                ],
            ),
            db,
        )
    assert exc.value.status_code == 403


async def test_create_character_missing_ability_score_rejected(
    db: AsyncSession, human_race_id: str, fighter_class_id: str
) -> None:
    """Fewer than six distinct ability scores is a validation error."""
    owner = await _make_user(db, email="player@example.com")
    member = await _make_membership(db, owner)
    service = CharacterService()

    incomplete_scores = _ability_scores()[:5]
    with pytest.raises(HTTPException) as exc:
        await service.create_character(
            owner.id,
            CharacterCreate(
                campaign_member_id=member.id,
                name="Incomplete",
                race_id=uuid.UUID(human_race_id),
                ability_scores=incomplete_scores,
                classes=[
                    CharacterClassCreate(class_definition_id=uuid.UUID(fighter_class_id))
                ],
            ),
            db,
        )
    assert exc.value.status_code == 422
