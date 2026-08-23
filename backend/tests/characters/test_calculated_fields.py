"""Tests for calculated (non-persisted) fields: ability modifiers, skill bonuses."""

import uuid

import pytest
from fastapi import HTTPException
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.campaigns.domain import CampaignRole
from app.campaigns.models import Campaign, CampaignMember
from app.catalog.domain import AbilityScore
from app.characters.domain import Skill
from app.characters.models import CharacterSkill
from app.characters.schemas import (
    CharacterAbilityScoreCreate,
    CharacterClassCreate,
    CharacterCreate,
)
from app.characters.service import CharacterService

# STR 16 (+3), DEX 14 (+2), CON 13 (+1), INT 10 (+0), WIS 8 (-1), CHA 12 (+1).
_KNOWN_SCORES = {
    AbilityScore.str: 16,
    AbilityScore.dex: 14,
    AbilityScore.con: 13,
    AbilityScore.int: 10,
    AbilityScore.wis: 8,
    AbilityScore.cha: 12,
}


def _ability_scores() -> list[CharacterAbilityScoreCreate]:
    return [
        CharacterAbilityScoreCreate(ability=ability, base_score=score)
        for ability, score in _KNOWN_SCORES.items()
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


async def test_ability_modifiers_match_5e_rules(
    db: AsyncSession, human_race_id: str, fighter_class_id: str
) -> None:
    """Each ability score's `modifier` follows the standard 5e formula."""
    owner = await _make_user(db, email="player@example.com")
    member = await _make_membership(db, owner)
    service = CharacterService()

    character = await service.create_character(
        owner.id,
        CharacterCreate(
            campaign_member_id=member.id,
            name="Rowan",
            race_id=uuid.UUID(human_race_id),
            ability_scores=_ability_scores(),
            classes=[
                CharacterClassCreate(class_definition_id=uuid.UUID(fighter_class_id))
            ],
        ),
        db,
    )

    modifiers = {s.ability: s.modifier for s in character.ability_scores}
    assert modifiers[AbilityScore.str] == 3
    assert modifiers[AbilityScore.dex] == 2
    assert modifiers[AbilityScore.con] == 1
    assert modifiers[AbilityScore.int] == 0
    assert modifiers[AbilityScore.wis] == -1
    assert modifiers[AbilityScore.cha] == 1


async def test_skill_bonus_reflects_proficiency_and_governing_ability(
    db: AsyncSession, human_race_id: str, fighter_class_id: str
) -> None:
    """A proficient skill's bonus is ability modifier + proficiency bonus."""
    owner = await _make_user(db, email="player@example.com")
    member = await _make_membership(db, owner)
    service = CharacterService()

    character = await service.create_character(
        owner.id,
        CharacterCreate(
            campaign_member_id=member.id,
            name="Rowan",
            race_id=uuid.UUID(human_race_id),
            ability_scores=_ability_scores(),
            classes=[
                CharacterClassCreate(class_definition_id=uuid.UUID(fighter_class_id))
            ],
        ),
        db,
    )
    assert character.proficiency_bonus == 2

    athletics = next(s for s in character.skills if s.skill == Skill.athletics)
    assert athletics.ability == AbilityScore.str
    assert not athletics.proficient
    assert athletics.bonus == 3  # unproficient: just the STR modifier

    # Mark Athletics proficient directly in the DB, then re-fetch via the
    # service to confirm the bonus recomputes (never trusted as stored data).
    await db.execute(
        update(CharacterSkill)
        .where(
            CharacterSkill.character_id == character.id,
            CharacterSkill.skill == Skill.athletics,
        )
        .values(proficient=True)
    )
    await db.commit()

    refreshed = await service.get_character(character.id, owner.id, db)
    refreshed_athletics = next(
        s for s in refreshed.skills if s.skill == Skill.athletics
    )
    assert refreshed_athletics.proficient
    assert refreshed_athletics.bonus == 5  # STR modifier (+3) + proficiency (+2)


async def test_get_character_visible_to_owner_and_campaign_dm(
    db: AsyncSession, human_race_id: str, fighter_class_id: str
) -> None:
    """The character's own player and the campaign's DM can both fetch it."""
    dm = await _make_user(db, email="dm@example.com")
    player = await _make_user(db, email="player@example.com")
    campaign = Campaign(name="Shared Table", owner_id=dm.id)
    db.add(campaign)
    await db.flush()
    dm_member = CampaignMember(
        campaign_id=campaign.id, user_id=dm.id, role=CampaignRole.dm
    )
    player_member = CampaignMember(
        campaign_id=campaign.id, user_id=player.id, role=CampaignRole.player
    )
    db.add_all([dm_member, player_member])
    await db.commit()
    await db.refresh(player_member)

    service = CharacterService()
    character = await service.create_character(
        player.id,
        CharacterCreate(
            campaign_member_id=player_member.id,
            name="Shared Sheet",
            race_id=uuid.UUID(human_race_id),
            ability_scores=_ability_scores(),
            classes=[
                CharacterClassCreate(class_definition_id=uuid.UUID(fighter_class_id))
            ],
        ),
        db,
    )

    by_owner = await service.get_character(character.id, player.id, db)
    assert by_owner.id == character.id
    by_dm = await service.get_character(character.id, dm.id, db)
    assert by_dm.id == character.id


async def test_get_character_not_visible_to_other_players(
    db: AsyncSession, human_race_id: str, fighter_class_id: str
) -> None:
    """A player in the same campaign but not the owner cannot view the sheet."""
    dm = await _make_user(db, email="dm@example.com")
    owner = await _make_user(db, email="owner@example.com")
    other_player = await _make_user(db, email="other@example.com")
    campaign = Campaign(name="Shared Table", owner_id=dm.id)
    db.add(campaign)
    await db.flush()
    owner_member = CampaignMember(
        campaign_id=campaign.id, user_id=owner.id, role=CampaignRole.player
    )
    other_member = CampaignMember(
        campaign_id=campaign.id, user_id=other_player.id, role=CampaignRole.player
    )
    db.add_all([owner_member, other_member])
    await db.commit()
    await db.refresh(owner_member)

    service = CharacterService()
    character = await service.create_character(
        owner.id,
        CharacterCreate(
            campaign_member_id=owner_member.id,
            name="Private Sheet",
            race_id=uuid.UUID(human_race_id),
            ability_scores=_ability_scores(),
            classes=[
                CharacterClassCreate(class_definition_id=uuid.UUID(fighter_class_id))
            ],
        ),
        db,
    )

    with pytest.raises(HTTPException) as exc:
        await service.get_character(character.id, other_player.id, db)
    assert exc.value.status_code == 403
