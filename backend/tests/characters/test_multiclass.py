"""Tests for adding a second class to a character (multiclassing)."""

import uuid

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.campaigns.domain import CampaignRole
from app.campaigns.models import Campaign, CampaignMember
from app.catalog.domain import AbilityScore
from app.characters.schemas import (
    CharacterAbilityScoreCreate,
    CharacterClassCreate,
    CharacterCreate,
)
from app.characters.service import CharacterService


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


def _scores(str_score: int, int_score: int) -> list[CharacterAbilityScoreCreate]:
    values = {
        AbilityScore.str: str_score,
        AbilityScore.dex: 10,
        AbilityScore.con: 10,
        AbilityScore.int: int_score,
        AbilityScore.wis: 10,
        AbilityScore.cha: 10,
    }
    return [
        CharacterAbilityScoreCreate(ability=ability, base_score=score)
        for ability, score in values.items()
    ]


async def _make_fighter(
    db: AsyncSession,
    owner: User,
    member: CampaignMember,
    human_race_id: str,
    fighter_class_id: str,
    *,
    str_score: int,
    int_score: int,
) -> uuid.UUID:
    service = CharacterService()
    character = await service.create_character(
        owner.id,
        CharacterCreate(
            campaign_member_id=member.id,
            name="Multiclasser",
            race_id=uuid.UUID(human_race_id),
            ability_scores=_scores(str_score, int_score),
            classes=[
                CharacterClassCreate(class_definition_id=uuid.UUID(fighter_class_id))
            ],
        ),
        db,
    )
    return character.id


async def test_multiclass_into_wizard_with_sufficient_int(
    db: AsyncSession, human_race_id: str, fighter_class_id: str, wizard_class_id: str
) -> None:
    """A Fighter with INT 13+ can multiclass into Wizard."""
    owner = await _make_user(db, email="player@example.com")
    member = await _make_membership(db, owner)
    character_id = await _make_fighter(
        db,
        owner,
        member,
        human_race_id,
        fighter_class_id,
        str_score=15,
        int_score=13,
    )

    service = CharacterService()
    updated = await service.add_class(
        character_id,
        owner.id,
        CharacterClassCreate(class_definition_id=uuid.UUID(wizard_class_id)),
        db,
    )

    assert len(updated.classes) == 2
    class_ids = {c.class_definition_id for c in updated.classes}
    assert uuid.UUID(wizard_class_id) in class_ids
    assert updated.level == 2  # 1 (fighter) + 1 (wizard)
    assert updated.proficiency_bonus == 2


async def test_multiclass_into_wizard_with_insufficient_int_rejected(
    db: AsyncSession, human_race_id: str, fighter_class_id: str, wizard_class_id: str
) -> None:
    """A Fighter with INT below 13 cannot multiclass into Wizard."""
    owner = await _make_user(db, email="player@example.com")
    member = await _make_membership(db, owner)
    character_id = await _make_fighter(
        db,
        owner,
        member,
        human_race_id,
        fighter_class_id,
        str_score=15,
        int_score=10,
    )

    service = CharacterService()
    with pytest.raises(HTTPException) as exc:
        await service.add_class(
            character_id,
            owner.id,
            CharacterClassCreate(class_definition_id=uuid.UUID(wizard_class_id)),
            db,
        )
    assert exc.value.status_code == 422


async def test_multiclass_rejects_class_the_character_already_has(
    db: AsyncSession, human_race_id: str, fighter_class_id: str
) -> None:
    """Adding a class the character already has is rejected, not silently merged."""
    owner = await _make_user(db, email="player@example.com")
    member = await _make_membership(db, owner)
    character_id = await _make_fighter(
        db,
        owner,
        member,
        human_race_id,
        fighter_class_id,
        str_score=15,
        int_score=13,
    )

    service = CharacterService()
    with pytest.raises(HTTPException) as exc:
        await service.add_class(
            character_id,
            owner.id,
            CharacterClassCreate(class_definition_id=uuid.UUID(fighter_class_id)),
            db,
        )
    assert exc.value.status_code == 409


async def test_multiclass_rejected_for_someone_elses_character(
    db: AsyncSession, human_race_id: str, fighter_class_id: str, wizard_class_id: str
) -> None:
    """A user cannot add a class to a character they don't own."""
    owner = await _make_user(db, email="owner@example.com")
    outsider = await _make_user(db, email="outsider@example.com")
    member = await _make_membership(db, owner)
    character_id = await _make_fighter(
        db,
        owner,
        member,
        human_race_id,
        fighter_class_id,
        str_score=15,
        int_score=13,
    )

    service = CharacterService()
    with pytest.raises(HTTPException) as exc:
        await service.add_class(
            character_id,
            outsider.id,
            CharacterClassCreate(class_definition_id=uuid.UUID(wizard_class_id)),
            db,
        )
    assert exc.value.status_code == 403
