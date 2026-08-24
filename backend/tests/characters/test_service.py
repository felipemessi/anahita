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
    CharacterSpellCreate,
    CharacterSpellUpdate,
)
from app.characters.service import CharacterService
from tests.characters.conftest import spell_ids_for_class

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


async def _create_character(
    db: AsyncSession,
    owner: User,
    member: CampaignMember,
    human_race_id: str,
    class_id: str,
) -> uuid.UUID:
    service = CharacterService()
    character = await service.create_character(
        owner.id,
        CharacterCreate(
            campaign_member_id=member.id,
            name="Caster",
            race_id=uuid.UUID(human_race_id),
            ability_scores=_ability_scores(),
            classes=[CharacterClassCreate(class_definition_id=uuid.UUID(class_id))],
        ),
        db,
    )
    return character.id


async def test_add_spell_prepared_caster_limit_enforced(
    db: AsyncSession, human_race_id: str, wizard_class_id: str
) -> None:
    """A prepared caster (Wizard) can't prepare more than ability mod + level."""
    owner = await _make_user(db, email="player@example.com")
    member = await _make_membership(db, owner)
    character_id = await _create_character(
        db, owner, member, human_race_id, wizard_class_id
    )
    # INT 12 -> +1 modifier; level 1 -> limit = max(1, 1 + 1) = 2.
    spell_ids = await spell_ids_for_class(db, wizard_class_id, level=1, limit=3)
    assert len(spell_ids) == 3
    service = CharacterService()

    for spell_id in spell_ids[:2]:
        await service.add_spell(
            character_id,
            owner.id,
            CharacterSpellCreate(
                spell_id=uuid.UUID(spell_id), prepared=True, source_class="wizard"
            ),
            db,
        )

    with pytest.raises(HTTPException) as exc:
        await service.add_spell(
            character_id,
            owner.id,
            CharacterSpellCreate(
                spell_id=uuid.UUID(spell_ids[2]), prepared=True, source_class="wizard"
            ),
            db,
        )
    assert exc.value.status_code == 422


async def test_add_spell_known_caster_limit_enforced(
    db: AsyncSession, human_race_id: str, sorcerer_class_id: str
) -> None:
    """A known caster (Sorcerer) can't know more spells than its table allows."""
    owner = await _make_user(db, email="player@example.com")
    member = await _make_membership(db, owner)
    character_id = await _create_character(
        db, owner, member, human_race_id, sorcerer_class_id
    )
    # Sorcerer knows 2 1st-level spells at level 1.
    spell_ids = await spell_ids_for_class(db, sorcerer_class_id, level=1, limit=3)
    assert len(spell_ids) == 3
    service = CharacterService()

    for spell_id in spell_ids[:2]:
        await service.add_spell(
            character_id,
            owner.id,
            CharacterSpellCreate(
                spell_id=uuid.UUID(spell_id), source_class="sorcerer"
            ),
            db,
        )

    with pytest.raises(HTTPException) as exc:
        await service.add_spell(
            character_id,
            owner.id,
            CharacterSpellCreate(
                spell_id=uuid.UUID(spell_ids[2]), source_class="sorcerer"
            ),
            db,
        )
    assert exc.value.status_code == 422


async def test_update_spell_toggle_prepared(
    db: AsyncSession, human_race_id: str, wizard_class_id: str
) -> None:
    """Toggling `prepared` on a known spell persists and re-checks the limit."""
    owner = await _make_user(db, email="player@example.com")
    member = await _make_membership(db, owner)
    character_id = await _create_character(
        db, owner, member, human_race_id, wizard_class_id
    )
    spell_ids = await spell_ids_for_class(db, wizard_class_id, level=1, limit=1)
    service = CharacterService()
    character = await service.add_spell(
        character_id,
        owner.id,
        CharacterSpellCreate(
            spell_id=uuid.UUID(spell_ids[0]), prepared=False, source_class="wizard"
        ),
        db,
    )
    entry_id = character.spells[0].id

    character = await service.update_spell(
        character_id, entry_id, owner.id, CharacterSpellUpdate(prepared=True), db
    )
    assert character.spells[0].prepared is True

    character = await service.update_spell(
        character_id, entry_id, owner.id, CharacterSpellUpdate(prepared=False), db
    )
    assert character.spells[0].prepared is False


async def test_remove_spell(
    db: AsyncSession, human_race_id: str, wizard_class_id: str
) -> None:
    """Removing a known spell drops it from the sheet and frees its slot."""
    owner = await _make_user(db, email="player@example.com")
    member = await _make_membership(db, owner)
    character_id = await _create_character(
        db, owner, member, human_race_id, wizard_class_id
    )
    spell_ids = await spell_ids_for_class(db, wizard_class_id, level=1, limit=1)
    service = CharacterService()
    character = await service.add_spell(
        character_id,
        owner.id,
        CharacterSpellCreate(spell_id=uuid.UUID(spell_ids[0]), source_class="wizard"),
        db,
    )
    entry_id = character.spells[0].id

    character = await service.remove_spell(character_id, entry_id, owner.id, db)
    assert character.spells == []


async def test_update_spell_wrong_owner_rejected(
    db: AsyncSession, human_race_id: str, wizard_class_id: str
) -> None:
    """A different player cannot toggle/remove another character's spells."""
    owner = await _make_user(db, email="owner@example.com")
    outsider = await _make_user(db, email="outsider@example.com")
    member = await _make_membership(db, owner)
    character_id = await _create_character(
        db, owner, member, human_race_id, wizard_class_id
    )
    spell_ids = await spell_ids_for_class(db, wizard_class_id, level=1, limit=1)
    service = CharacterService()
    character = await service.add_spell(
        character_id,
        owner.id,
        CharacterSpellCreate(spell_id=uuid.UUID(spell_ids[0]), source_class="wizard"),
        db,
    )
    entry_id = character.spells[0].id

    with pytest.raises(HTTPException) as exc:
        await service.update_spell(
            character_id,
            entry_id,
            outsider.id,
            CharacterSpellUpdate(prepared=True),
            db,
        )
    assert exc.value.status_code == 403

    with pytest.raises(HTTPException) as exc:
        await service.remove_spell(character_id, entry_id, outsider.id, db)
    assert exc.value.status_code == 403
