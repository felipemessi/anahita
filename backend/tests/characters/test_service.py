"""Integration tests for CharacterService using SQLite in-memory database."""

import uuid

import pytest
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.campaigns.domain import CampaignRole
from app.campaigns.models import Campaign, CampaignMember
from app.catalog.domain import AbilityScore
from app.catalog.models import Race, Spell, SpellClass
from app.characters.schemas import (
    CharacterAbilityScoreCreate,
    CharacterClassCreate,
    CharacterCreate,
    CharacterCurrencyRequest,
    CharacterEquipmentCreate,
    CharacterEquipmentUpdate,
    CharacterRead,
    CharacterRestRequest,
    CharacterSpellCastRequest,
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
    *,
    level: int = 1,
) -> uuid.UUID:
    service = CharacterService()
    character = await service.create_character(
        owner.id,
        CharacterCreate(
            campaign_member_id=member.id,
            name="Caster",
            race_id=uuid.UUID(human_race_id),
            ability_scores=_ability_scores(),
            classes=[
                CharacterClassCreate(
                    class_definition_id=uuid.UUID(class_id), level=level
                )
            ],
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


async def test_cast_spell_consumes_slot(
    db: AsyncSession, human_race_id: str, sorcerer_class_id: str
) -> None:
    """Casting a leveled spell at its own level consumes one slot of that level."""
    owner = await _make_user(db, email="player@example.com")
    member = await _make_membership(db, owner)
    character_id = await _create_character(
        db, owner, member, human_race_id, sorcerer_class_id
    )
    spell_ids = await spell_ids_for_class(db, sorcerer_class_id, level=1, limit=1)
    service = CharacterService()
    character = await service.add_spell(
        character_id,
        owner.id,
        CharacterSpellCreate(spell_id=uuid.UUID(spell_ids[0]), source_class="sorcerer"),
        db,
    )
    entry_id = character.spells[0].id

    character = await service.cast_spell(
        character_id, entry_id, owner.id, CharacterSpellCastRequest(), db
    )
    slot = next(s for s in character.spell_slots if s.spell_level == 1)
    # Level-1 Sorcerer has 2 first-level slots.
    assert slot.used == 1
    assert slot.max == 2


async def test_cast_cantrip_does_not_consume_slot(
    db: AsyncSession, human_race_id: str, sorcerer_class_id: str
) -> None:
    """Casting a cantrip never touches spell slots."""
    owner = await _make_user(db, email="player@example.com")
    member = await _make_membership(db, owner)
    character_id = await _create_character(
        db, owner, member, human_race_id, sorcerer_class_id
    )
    cantrip_ids = await spell_ids_for_class(db, sorcerer_class_id, level=0, limit=1)
    service = CharacterService()
    character = await service.add_spell(
        character_id,
        owner.id,
        CharacterSpellCreate(
            spell_id=uuid.UUID(cantrip_ids[0]), source_class="sorcerer"
        ),
        db,
    )
    entry_id = character.spells[0].id

    character = await service.cast_spell(
        character_id, entry_id, owner.id, CharacterSpellCastRequest(), db
    )
    assert all(s.used == 0 for s in character.spell_slots)


async def test_cast_spell_no_slot_available_rejected(
    db: AsyncSession, human_race_id: str, sorcerer_class_id: str
) -> None:
    """Casting once every slot at that level is used is rejected (422)."""
    owner = await _make_user(db, email="player@example.com")
    member = await _make_membership(db, owner)
    character_id = await _create_character(
        db, owner, member, human_race_id, sorcerer_class_id
    )
    spell_ids = await spell_ids_for_class(db, sorcerer_class_id, level=1, limit=1)
    service = CharacterService()
    character = await service.add_spell(
        character_id,
        owner.id,
        CharacterSpellCreate(spell_id=uuid.UUID(spell_ids[0]), source_class="sorcerer"),
        db,
    )
    entry_id = character.spells[0].id

    # Level-1 Sorcerer has 2 first-level slots — exhaust them.
    for _ in range(2):
        character = await service.cast_spell(
            character_id, entry_id, owner.id, CharacterSpellCastRequest(), db
        )

    with pytest.raises(HTTPException) as exc:
        await service.cast_spell(
            character_id, entry_id, owner.id, CharacterSpellCastRequest(), db
        )
    assert exc.value.status_code == 422


async def test_cast_spell_upcast_consumes_higher_level_slot(
    db: AsyncSession, human_race_id: str, sorcerer_class_id: str
) -> None:
    """Casting at a higher level than the spell's own consumes that level's slot."""
    owner = await _make_user(db, email="player@example.com")
    member = await _make_membership(db, owner)
    # A level-3 Sorcerer has 2nd-level slots to upcast a 1st-level spell into.
    character_id = await _create_character(
        db, owner, member, human_race_id, sorcerer_class_id, level=3
    )
    spell_ids = await spell_ids_for_class(db, sorcerer_class_id, level=1, limit=1)
    service = CharacterService()
    character = await service.add_spell(
        character_id,
        owner.id,
        CharacterSpellCreate(spell_id=uuid.UUID(spell_ids[0]), source_class="sorcerer"),
        db,
    )
    entry_id = character.spells[0].id

    character = await service.cast_spell(
        character_id,
        entry_id,
        owner.id,
        CharacterSpellCastRequest(cast_at_level=2),
        db,
    )
    level_1_slot = next(s for s in character.spell_slots if s.spell_level == 1)
    level_2_slot = next(s for s in character.spell_slots if s.spell_level == 2)
    assert level_1_slot.used == 0
    assert level_2_slot.used == 1


async def test_cast_spell_below_own_level_rejected(
    db: AsyncSession, human_race_id: str, sorcerer_class_id: str
) -> None:
    """Casting a spell at a level lower than its own is rejected (422)."""
    owner = await _make_user(db, email="player@example.com")
    member = await _make_membership(db, owner)
    character_id = await _create_character(
        db, owner, member, human_race_id, sorcerer_class_id, level=3
    )
    spell_ids = await spell_ids_for_class(db, sorcerer_class_id, level=2, limit=1)
    service = CharacterService()
    character = await service.add_spell(
        character_id,
        owner.id,
        CharacterSpellCreate(spell_id=uuid.UUID(spell_ids[0]), source_class="sorcerer"),
        db,
    )
    entry_id = character.spells[0].id

    with pytest.raises(HTTPException) as exc:
        await service.cast_spell(
            character_id,
            entry_id,
            owner.id,
            CharacterSpellCastRequest(cast_at_level=1),
            db,
        )
    assert exc.value.status_code == 422


async def test_cast_ritual_does_not_consume_slot(
    db: AsyncSession, human_race_id: str, wizard_class_id: str
) -> None:
    """Casting a ritual spell never consumes a slot, even without preparing it."""
    owner = await _make_user(db, email="player@example.com")
    member = await _make_membership(db, owner)
    character_id = await _create_character(
        db, owner, member, human_race_id, wizard_class_id
    )
    ritual_result = await db.execute(
        select(Spell.id)
        .join(SpellClass, SpellClass.spell_id == Spell.id)
        .where(
            SpellClass.class_definition_id == uuid.UUID(wizard_class_id),
            Spell.level == 1,
            Spell.ritual.is_(True),
        )
        .limit(1)
    )
    ritual_spell_id = ritual_result.scalar_one()
    service = CharacterService()
    character = await service.add_spell(
        character_id,
        owner.id,
        CharacterSpellCreate(
            spell_id=ritual_spell_id, prepared=False, source_class="wizard"
        ),
        db,
    )
    entry_id = character.spells[0].id

    character = await service.cast_spell(
        character_id,
        entry_id,
        owner.id,
        CharacterSpellCastRequest(as_ritual=True),
        db,
    )
    assert all(s.used == 0 for s in character.spell_slots)


async def test_cast_unprepared_non_ritual_spell_rejected(
    db: AsyncSession, human_race_id: str, wizard_class_id: str
) -> None:
    """A prepared caster can't cast a known but unprepared spell normally."""
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

    with pytest.raises(HTTPException) as exc:
        await service.cast_spell(
            character_id, entry_id, owner.id, CharacterSpellCastRequest(), db
        )
    assert exc.value.status_code == 422


async def test_long_rest_restores_all_spell_slots(
    db: AsyncSession, human_race_id: str, sorcerer_class_id: str
) -> None:
    """A long rest zeroes every spell slot's `used` count."""
    owner = await _make_user(db, email="player@example.com")
    member = await _make_membership(db, owner)
    character_id = await _create_character(
        db, owner, member, human_race_id, sorcerer_class_id
    )
    spell_ids = await spell_ids_for_class(db, sorcerer_class_id, level=1, limit=1)
    service = CharacterService()
    character = await service.add_spell(
        character_id,
        owner.id,
        CharacterSpellCreate(spell_id=uuid.UUID(spell_ids[0]), source_class="sorcerer"),
        db,
    )
    entry_id = character.spells[0].id
    await service.cast_spell(
        character_id, entry_id, owner.id, CharacterSpellCastRequest(), db
    )

    character = await service.rest(
        character_id, owner.id, CharacterRestRequest(rest_type="long"), db
    )
    assert all(s.used == 0 for s in character.spell_slots)


async def test_short_rest_does_not_restore_spell_slots(
    db: AsyncSession, human_race_id: str, sorcerer_class_id: str
) -> None:
    """A short rest leaves spell slots untouched (no Warlock-style recovery here)."""
    owner = await _make_user(db, email="player@example.com")
    member = await _make_membership(db, owner)
    character_id = await _create_character(
        db, owner, member, human_race_id, sorcerer_class_id
    )
    spell_ids = await spell_ids_for_class(db, sorcerer_class_id, level=1, limit=1)
    service = CharacterService()
    character = await service.add_spell(
        character_id,
        owner.id,
        CharacterSpellCreate(spell_id=uuid.UUID(spell_ids[0]), source_class="sorcerer"),
        db,
    )
    entry_id = character.spells[0].id
    await service.cast_spell(
        character_id, entry_id, owner.id, CharacterSpellCastRequest(), db
    )

    character = await service.rest(
        character_id, owner.id, CharacterRestRequest(rest_type="short"), db
    )
    used_slot = next(s for s in character.spell_slots if s.spell_level == 1)
    assert used_slot.used == 1


async def test_update_equipment_toggle_and_quantity(
    db: AsyncSession, human_race_id: str, fighter_class_id: str, longsword_item_id: str
) -> None:
    """Editing an inventory item updates equipped/attunement/quantity."""
    owner = await _make_user(db, email="player@example.com")
    member = await _make_membership(db, owner)
    character_id = await _create_character(
        db, owner, member, human_race_id, fighter_class_id
    )
    service = CharacterService()
    character = await service.add_equipment(
        character_id,
        owner.id,
        CharacterEquipmentCreate(item_id=uuid.UUID(longsword_item_id), quantity=1),
        db,
    )
    entry_id = character.equipment[0].id

    character = await service.update_equipment(
        character_id,
        entry_id,
        owner.id,
        CharacterEquipmentUpdate(equipped=True, quantity=2),
        db,
    )
    assert character.equipment[0].equipped is True
    assert character.equipment[0].quantity == 2


async def test_remove_equipment(
    db: AsyncSession, human_race_id: str, fighter_class_id: str, longsword_item_id: str
) -> None:
    """Removing an item drops it from the character's inventory."""
    owner = await _make_user(db, email="player@example.com")
    member = await _make_membership(db, owner)
    character_id = await _create_character(
        db, owner, member, human_race_id, fighter_class_id
    )
    service = CharacterService()
    character = await service.add_equipment(
        character_id,
        owner.id,
        CharacterEquipmentCreate(item_id=uuid.UUID(longsword_item_id)),
        db,
    )
    entry_id = character.equipment[0].id

    character = await service.remove_equipment(character_id, entry_id, owner.id, db)
    assert character.equipment == []


async def test_update_equipment_wrong_owner_rejected(
    db: AsyncSession, human_race_id: str, fighter_class_id: str, longsword_item_id: str
) -> None:
    """A different player cannot edit/remove another character's items."""
    owner = await _make_user(db, email="owner@example.com")
    outsider = await _make_user(db, email="outsider@example.com")
    member = await _make_membership(db, owner)
    character_id = await _create_character(
        db, owner, member, human_race_id, fighter_class_id
    )
    service = CharacterService()
    character = await service.add_equipment(
        character_id,
        owner.id,
        CharacterEquipmentCreate(item_id=uuid.UUID(longsword_item_id)),
        db,
    )
    entry_id = character.equipment[0].id

    with pytest.raises(HTTPException) as exc:
        await service.update_equipment(
            character_id,
            entry_id,
            outsider.id,
            CharacterEquipmentUpdate(equipped=True),
            db,
        )
    assert exc.value.status_code == 403

    with pytest.raises(HTTPException) as exc:
        await service.remove_equipment(character_id, entry_id, outsider.id, db)
    assert exc.value.status_code == 403


async def test_update_currency_gain_and_spend(
    db: AsyncSession, human_race_id: str, fighter_class_id: str
) -> None:
    """Currency gain/spend deltas are reflected in the character's balance."""
    owner = await _make_user(db, email="player@example.com")
    member = await _make_membership(db, owner)
    character_id = await _create_character(
        db, owner, member, human_race_id, fighter_class_id
    )
    service = CharacterService()

    character = await service.update_currency(
        character_id, owner.id, CharacterCurrencyRequest(delta=500), db
    )
    assert character.currency_cp == 500

    character = await service.update_currency(
        character_id, owner.id, CharacterCurrencyRequest(delta=-200), db
    )
    assert character.currency_cp == 300


async def test_update_currency_negative_balance_rejected(
    db: AsyncSession, human_race_id: str, fighter_class_id: str
) -> None:
    """Spending more than the current balance is rejected (422)."""
    owner = await _make_user(db, email="player@example.com")
    member = await _make_membership(db, owner)
    character_id = await _create_character(
        db, owner, member, human_race_id, fighter_class_id
    )
    service = CharacterService()

    with pytest.raises(HTTPException) as exc:
        await service.update_currency(
            character_id, owner.id, CharacterCurrencyRequest(delta=-1), db
        )
    assert exc.value.status_code == 422


async def test_list_characters_hides_others_full_sheet_from_player(
    db: AsyncSession, human_race_id: str, fighter_class_id: str
) -> None:
    """A player sees only a summary of another player's character."""
    dm = await _make_user(db, email="dm@example.com")
    owner_a = await _make_user(db, email="a@example.com")
    owner_b = await _make_user(db, email="b@example.com")
    campaign = Campaign(name="Shared Table", owner_id=dm.id)
    db.add(campaign)
    await db.flush()
    member_a = CampaignMember(
        campaign_id=campaign.id, user_id=owner_a.id, role=CampaignRole.player
    )
    member_b = CampaignMember(
        campaign_id=campaign.id, user_id=owner_b.id, role=CampaignRole.player
    )
    db.add_all([member_a, member_b])
    await db.commit()
    await db.refresh(member_a)
    await db.refresh(member_b)

    service = CharacterService()
    await service.create_character(
        owner_a.id,
        CharacterCreate(
            campaign_member_id=member_a.id,
            name="Aldric",
            race_id=uuid.UUID(human_race_id),
            ability_scores=_ability_scores(),
            classes=[
                CharacterClassCreate(class_definition_id=uuid.UUID(fighter_class_id))
            ],
        ),
        db,
    )
    await service.create_character(
        owner_b.id,
        CharacterCreate(
            campaign_member_id=member_b.id,
            name="Brenna",
            race_id=uuid.UUID(human_race_id),
            ability_scores=_ability_scores(),
            classes=[
                CharacterClassCreate(class_definition_id=uuid.UUID(fighter_class_id))
            ],
        ),
        db,
    )

    characters = await service.list_characters_for_campaign(campaign.id, owner_a.id, db)
    by_name = {c.name: c for c in characters}
    assert isinstance(by_name["Aldric"], CharacterRead)
    assert hasattr(by_name["Aldric"], "hit_point_max")
    assert not hasattr(by_name["Brenna"], "hit_point_max")
    assert not hasattr(by_name["Brenna"], "ability_scores")


async def test_list_characters_dm_sees_full_sheets(
    db: AsyncSession, human_race_id: str, fighter_class_id: str
) -> None:
    """The campaign's DM always sees every character's full sheet."""
    owner = await _make_user(db, email="dm-owner@example.com")
    dm_user = await _make_user(db, email="dm@example.com")
    member = await _make_membership(db, owner)
    campaign_result = await db.execute(
        select(Campaign).where(Campaign.owner_id == owner.id)
    )
    campaign = campaign_result.scalar_one()
    dm_member = CampaignMember(
        campaign_id=campaign.id, user_id=dm_user.id, role=CampaignRole.dm
    )
    db.add(dm_member)
    await db.commit()

    service = CharacterService()
    await service.create_character(
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

    characters = await service.list_characters_for_campaign(campaign.id, dm_user.id, db)
    assert hasattr(characters[0], "hit_point_max")
