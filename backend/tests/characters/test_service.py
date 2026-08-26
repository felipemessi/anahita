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
from app.catalog.models import Feat, Feature, Race, Spell, SpellClass
from app.characters.domain import AbilityGenerationMethod, Skill
from app.characters.models import CharacterSkill
from app.characters.schemas import (
    CharacterAbilityScoreCreate,
    CharacterClassCreate,
    CharacterConcentrationRequest,
    CharacterCreate,
    CharacterCurrencyRequest,
    CharacterDeathSaveRequest,
    CharacterEquipmentCreate,
    CharacterEquipmentUpdate,
    CharacterFeatureChoiceInput,
    CharacterHitDiceSpend,
    CharacterLevelUpRequest,
    CharacterRead,
    CharacterRestRequest,
    CharacterSpellCastRequest,
    CharacterSpellCreate,
    CharacterSpellUpdate,
    CharacterUpdate,
)
from app.characters.service import CharacterService
from tests.characters.conftest import spell_id_by_index, spell_ids_for_class

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


async def _spell_id_for_class(
    db: AsyncSession, class_id: str, *, level: int, concentration: bool
) -> str:
    """Return one spell id of `level` castable by `class_id` matching `concentration`."""
    result = await db.execute(
        select(Spell.id)
        .join(SpellClass, SpellClass.spell_id == Spell.id)
        .where(
            SpellClass.class_definition_id == uuid.UUID(class_id),
            Spell.level == level,
            Spell.concentration == concentration,
        )
        .limit(1)
    )
    return str(result.scalars().one())


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
                    CharacterClassCreate(
                        class_definition_id=uuid.UUID(fighter_class_id)
                    )
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
                    CharacterClassCreate(
                        class_definition_id=uuid.UUID(fighter_class_id)
                    )
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
                    CharacterClassCreate(
                        class_definition_id=uuid.UUID(fighter_class_id)
                    )
                ],
            ),
            db,
        )
    assert exc.value.status_code == 422


async def test_create_character_with_standard_array_persists_method(
    db: AsyncSession, human_race_id: str, fighter_class_id: str
) -> None:
    """A character created with `standard_array` persists the method used."""
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
            generation_method=AbilityGenerationMethod.standard_array,
        ),
        db,
    )

    assert character.generation_method == AbilityGenerationMethod.standard_array


async def test_create_character_point_buy_over_budget_rejected(
    db: AsyncSession, human_race_id: str, fighter_class_id: str
) -> None:
    """Declaring `point_buy` with an over-budget spend is a 422, not created."""
    owner = await _make_user(db, email="player@example.com")
    member = await _make_membership(db, owner)
    service = CharacterService()

    over_budget_scores = [
        CharacterAbilityScoreCreate(ability=ability, base_score=15)
        for ability in AbilityScore
    ]
    with pytest.raises(HTTPException) as exc:
        await service.create_character(
            owner.id,
            CharacterCreate(
                campaign_member_id=member.id,
                name="Overspent",
                race_id=uuid.UUID(human_race_id),
                ability_scores=over_budget_scores,
                classes=[
                    CharacterClassCreate(
                        class_definition_id=uuid.UUID(fighter_class_id)
                    )
                ],
                generation_method=AbilityGenerationMethod.point_buy,
            ),
            db,
        )
    assert exc.value.status_code == 422


async def test_create_character_custom_method_skips_validation(
    db: AsyncSession, human_race_id: str, fighter_class_id: str
) -> None:
    """`custom` accepts any ability score combination, even an unusual one."""
    owner = await _make_user(db, email="player@example.com")
    member = await _make_membership(db, owner)
    service = CharacterService()

    unusual_scores = [
        CharacterAbilityScoreCreate(ability=ability, base_score=3)
        for ability in AbilityScore
    ]
    character = await service.create_character(
        owner.id,
        CharacterCreate(
            campaign_member_id=member.id,
            name="Unlucky",
            race_id=uuid.UUID(human_race_id),
            ability_scores=unusual_scores,
            classes=[
                CharacterClassCreate(class_definition_id=uuid.UUID(fighter_class_id))
            ],
            generation_method=AbilityGenerationMethod.custom,
        ),
        db,
    )

    assert character.generation_method == AbilityGenerationMethod.custom


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
            CharacterSpellCreate(spell_id=uuid.UUID(spell_id), source_class="sorcerer"),
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

    character = (
        await service.cast_spell(
            character_id, entry_id, owner.id, CharacterSpellCastRequest(), db
        )
    ).character
    slot = next(s for s in character.spell_slots if s.spell_level == 1)
    # Level-1 Sorcerer has 2 first-level slots.
    assert slot.used == 1
    assert slot.max == 2


async def test_cast_saving_throw_spell_returns_save_dc(
    db: AsyncSession, human_race_id: str, sorcerer_class_id: str
) -> None:
    """Casting a saving_throw spell returns 8 + proficiency + spellcasting mod."""
    owner = await _make_user(db, email="player@example.com")
    member = await _make_membership(db, owner)
    character_id = await _create_character(
        db, owner, member, human_race_id, sorcerer_class_id, level=5
    )
    fireball_id = await spell_id_by_index(db, "fireball")
    service = CharacterService()
    character = await service.add_spell(
        character_id,
        owner.id,
        CharacterSpellCreate(spell_id=uuid.UUID(fireball_id), source_class="sorcerer"),
        db,
    )
    entry_id = character.spells[0].id

    result = await service.cast_spell(
        character_id, entry_id, owner.id, CharacterSpellCastRequest(), db
    )

    # `_create_character(level=5)` only sets the class's own level (needed
    # for a level-3 spell slot to exist) — `Character.level`/
    # `proficiency_bonus` are set from `CharacterCreate.level`, which
    # defaults to 1 here, so proficiency stays +2.
    # 8 + proficiency (+2) + CHA mod (8 -> -1) = 9.
    assert result.save_dc == 9


async def test_cast_attack_roll_spell_returns_no_save_dc(
    db: AsyncSession, human_race_id: str, sorcerer_class_id: str
) -> None:
    """Casting an attack_roll spell (Fire Bolt) never returns a save_dc."""
    owner = await _make_user(db, email="player@example.com")
    member = await _make_membership(db, owner)
    character_id = await _create_character(
        db, owner, member, human_race_id, sorcerer_class_id
    )
    fire_bolt_id = await spell_id_by_index(db, "fire-bolt")
    service = CharacterService()
    character = await service.add_spell(
        character_id,
        owner.id,
        CharacterSpellCreate(spell_id=uuid.UUID(fire_bolt_id), source_class="sorcerer"),
        db,
    )
    entry_id = character.spells[0].id

    result = await service.cast_spell(
        character_id, entry_id, owner.id, CharacterSpellCastRequest(), db
    )

    assert result.save_dc is None


async def test_cast_only_spell_returns_no_save_dc(
    db: AsyncSession, human_race_id: str, sorcerer_class_id: str
) -> None:
    """Casting a cast_only spell (Mage Armor) never returns a save_dc."""
    owner = await _make_user(db, email="player@example.com")
    member = await _make_membership(db, owner)
    character_id = await _create_character(
        db, owner, member, human_race_id, sorcerer_class_id
    )
    mage_armor_id = await spell_id_by_index(db, "mage-armor")
    service = CharacterService()
    character = await service.add_spell(
        character_id,
        owner.id,
        CharacterSpellCreate(
            spell_id=uuid.UUID(mage_armor_id), source_class="sorcerer"
        ),
        db,
    )
    entry_id = character.spells[0].id

    result = await service.cast_spell(
        character_id, entry_id, owner.id, CharacterSpellCastRequest(), db
    )

    assert result.save_dc is None


async def test_cast_spell_echoes_target_participant_id(
    db: AsyncSession, human_race_id: str, sorcerer_class_id: str
) -> None:
    """`target_participant_id` is echoed back unchanged, unvalidated."""
    owner = await _make_user(db, email="player@example.com")
    member = await _make_membership(db, owner)
    character_id = await _create_character(
        db, owner, member, human_race_id, sorcerer_class_id
    )
    fire_bolt_id = await spell_id_by_index(db, "fire-bolt")
    service = CharacterService()
    character = await service.add_spell(
        character_id,
        owner.id,
        CharacterSpellCreate(spell_id=uuid.UUID(fire_bolt_id), source_class="sorcerer"),
        db,
    )
    entry_id = character.spells[0].id
    target_id = uuid.uuid4()

    result = await service.cast_spell(
        character_id,
        entry_id,
        owner.id,
        CharacterSpellCastRequest(target_participant_id=target_id),
        db,
    )

    assert result.target_participant_id == target_id


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

    character = (
        await service.cast_spell(
            character_id, entry_id, owner.id, CharacterSpellCastRequest(), db
        )
    ).character
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
        character = (
            await service.cast_spell(
                character_id, entry_id, owner.id, CharacterSpellCastRequest(), db
            )
        ).character

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

    character = (
        await service.cast_spell(
            character_id,
            entry_id,
            owner.id,
            CharacterSpellCastRequest(cast_at_level=2),
            db,
        )
    ).character
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

    character = (
        await service.cast_spell(
            character_id,
            entry_id,
            owner.id,
            CharacterSpellCastRequest(as_ritual=True),
            db,
        )
    ).character
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

    character = (await service.rest(
        character_id, owner.id, CharacterRestRequest(rest_type="long"), db
    )).character
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

    character = (await service.rest(
        character_id, owner.id, CharacterRestRequest(rest_type="short"), db
    )).character
    used_slot = next(s for s in character.spell_slots if s.spell_level == 1)
    assert used_slot.used == 1


async def test_short_rest_spend_hit_dice_heals_and_tracks_usage(
    db: AsyncSession, human_race_id: str, fighter_class_id: str
) -> None:
    """Spending hit dice on a short rest heals and marks the dice used."""
    owner = await _make_user(db, email="player@example.com")
    member = await _make_membership(db, owner)
    character_id = await _create_character(
        db, owner, member, human_race_id, fighter_class_id, level=3
    )
    service = CharacterService()
    character = await service.update_character(
        character_id,
        owner.id,
        CharacterUpdate(hit_point_current=1),
        db,
    )
    class_entry_id = character.classes[0].id

    character = (await service.rest(
        character_id,
        owner.id,
        CharacterRestRequest(
            rest_type="short",
            hit_dice_spent=[
                CharacterHitDiceSpend(
                    character_class_id=class_entry_id, count=2, manual_roll=7
                )
            ],
        ),
        db,
    )).character

    assert character.hit_point_current == 8  # 1 + 7 (well under hit_point_max of 11)
    assert character.classes[0].hit_dice_used == 2


async def test_short_rest_spend_hit_dice_caps_at_max_hp(
    db: AsyncSession, human_race_id: str, fighter_class_id: str
) -> None:
    """Healing from hit dice never exceeds `hit_point_max`."""
    owner = await _make_user(db, email="player@example.com")
    member = await _make_membership(db, owner)
    character_id = await _create_character(
        db, owner, member, human_race_id, fighter_class_id, level=3
    )
    service = CharacterService()
    character = await service.update_character(
        character_id,
        owner.id,
        CharacterUpdate(hit_point_current=10),
        db,
    )
    class_entry_id = character.classes[0].id

    character = (await service.rest(
        character_id,
        owner.id,
        CharacterRestRequest(
            rest_type="short",
            hit_dice_spent=[
                CharacterHitDiceSpend(
                    character_class_id=class_entry_id, count=1, manual_roll=20
                )
            ],
        ),
        db,
    )).character

    assert character.hit_point_current == 11  # hit_point_max, not 30


async def test_short_rest_spend_more_hit_dice_than_available_rejected(
    db: AsyncSession, human_race_id: str, fighter_class_id: str
) -> None:
    """Spending more hit dice than the class has left is a 422."""
    owner = await _make_user(db, email="player@example.com")
    member = await _make_membership(db, owner)
    character_id = await _create_character(
        db, owner, member, human_race_id, fighter_class_id, level=1
    )
    service = CharacterService()
    character = await service.get_character(character_id, owner.id, db)
    class_entry_id = character.classes[0].id

    with pytest.raises(HTTPException) as exc:
        await service.rest(
            character_id,
            owner.id,
            CharacterRestRequest(
                rest_type="short",
                hit_dice_spent=[
                    CharacterHitDiceSpend(
                        character_class_id=class_entry_id, count=2, manual_roll=10
                    )
                ],
            ),
            db,
        )
    assert exc.value.status_code == 422


async def test_long_rest_restores_half_hit_dice_minimum_one(
    db: AsyncSession, human_race_id: str, fighter_class_id: str
) -> None:
    """A long rest restores up to half the character's total hit dice (min 1)."""
    owner = await _make_user(db, email="player@example.com")
    member = await _make_membership(db, owner)
    character_id = await _create_character(
        db, owner, member, human_race_id, fighter_class_id, level=4
    )
    service = CharacterService()
    character = await service.update_character(
        character_id, owner.id, CharacterUpdate(hit_point_current=1), db
    )
    class_entry_id = character.classes[0].id

    # Spend all 4 hit dice on a short rest first.
    character = (await service.rest(
        character_id,
        owner.id,
        CharacterRestRequest(
            rest_type="short",
            hit_dice_spent=[
                CharacterHitDiceSpend(
                    character_class_id=class_entry_id, count=4, manual_roll=1
                )
            ],
        ),
        db,
    )).character
    assert character.classes[0].hit_dice_used == 4

    # Long rest restores half of 4 = 2.
    character = (await service.rest(
        character_id, owner.id, CharacterRestRequest(rest_type="long"), db
    )).character
    assert character.classes[0].hit_dice_used == 2


async def test_death_save_natural_20_restores_1_hp(
    db: AsyncSession, human_race_id: str, fighter_class_id: str
) -> None:
    """A natural 20 on a death save restores 1 HP and resets the track."""
    owner = await _make_user(db, email="player@example.com")
    member = await _make_membership(db, owner)
    character_id = await _create_character(
        db, owner, member, human_race_id, fighter_class_id
    )
    service = CharacterService()
    await service.update_character(
        character_id, owner.id, CharacterUpdate(hit_point_current=0), db
    )

    character = (
        await service.death_save(
            character_id, owner.id, CharacterDeathSaveRequest(manual_roll=20), db
        )
    ).character
    assert character.hit_point_current == 1
    assert character.death_save_successes == 0
    assert character.death_save_failures == 0
    assert character.is_dead is False


async def test_death_save_natural_1_counts_two_failures(
    db: AsyncSession, human_race_id: str, fighter_class_id: str
) -> None:
    """A natural 1 on a death save counts as two failures."""
    owner = await _make_user(db, email="player@example.com")
    member = await _make_membership(db, owner)
    character_id = await _create_character(
        db, owner, member, human_race_id, fighter_class_id
    )
    service = CharacterService()
    await service.update_character(
        character_id, owner.id, CharacterUpdate(hit_point_current=0), db
    )

    character = (
        await service.death_save(
            character_id, owner.id, CharacterDeathSaveRequest(manual_roll=1), db
        )
    ).character
    assert character.death_save_failures == 2
    assert character.is_dead is False


async def test_death_save_three_failures_marks_dead(
    db: AsyncSession, human_race_id: str, fighter_class_id: str
) -> None:
    """A sequence of failing death saves eventually marks the character dead."""
    owner = await _make_user(db, email="player@example.com")
    member = await _make_membership(db, owner)
    character_id = await _create_character(
        db, owner, member, human_race_id, fighter_class_id
    )
    service = CharacterService()
    await service.update_character(
        character_id, owner.id, CharacterUpdate(hit_point_current=0), db
    )

    for _ in range(3):
        character = (
            await service.death_save(
                character_id, owner.id, CharacterDeathSaveRequest(manual_roll=5), db
            )
        ).character
    assert character.death_save_failures == 3
    assert character.is_dead is True


async def test_death_save_three_successes_stabilizes(
    db: AsyncSession, human_race_id: str, fighter_class_id: str
) -> None:
    """A sequence of successful death saves stabilizes and resets the track."""
    owner = await _make_user(db, email="player@example.com")
    member = await _make_membership(db, owner)
    character_id = await _create_character(
        db, owner, member, human_race_id, fighter_class_id
    )
    service = CharacterService()
    await service.update_character(
        character_id, owner.id, CharacterUpdate(hit_point_current=0), db
    )

    for _ in range(3):
        character = (
            await service.death_save(
                character_id, owner.id, CharacterDeathSaveRequest(manual_roll=15), db
            )
        ).character
    assert character.death_save_successes == 0
    assert character.death_save_failures == 0
    assert character.is_dead is False
    assert character.hit_point_current == 0


async def test_death_save_rejected_above_zero_hp(
    db: AsyncSession, human_race_id: str, fighter_class_id: str
) -> None:
    """Death saves are only valid at 0 hit points."""
    owner = await _make_user(db, email="player@example.com")
    member = await _make_membership(db, owner)
    character_id = await _create_character(
        db, owner, member, human_race_id, fighter_class_id
    )
    service = CharacterService()

    with pytest.raises(HTTPException) as exc:
        await service.death_save(
            character_id, owner.id, CharacterDeathSaveRequest(manual_roll=15), db
        )
    assert exc.value.status_code == 422


async def test_damage_at_zero_hp_counts_death_save_failure(
    db: AsyncSession, human_race_id: str, fighter_class_id: str
) -> None:
    """Taking damage while already at 0 HP (still floored at 0) is a failure."""
    owner = await _make_user(db, email="player@example.com")
    member = await _make_membership(db, owner)
    character_id = await _create_character(
        db, owner, member, human_race_id, fighter_class_id
    )
    service = CharacterService()
    await service.update_character(
        character_id, owner.id, CharacterUpdate(hit_point_current=0), db
    )

    character = await service.update_character(
        character_id, owner.id, CharacterUpdate(hit_point_current=0), db
    )
    assert character.death_save_failures == 1


async def test_healing_above_zero_resets_death_save_counters(
    db: AsyncSession, human_race_id: str, fighter_class_id: str
) -> None:
    """Healing above 0 HP resets the death-save track."""
    owner = await _make_user(db, email="player@example.com")
    member = await _make_membership(db, owner)
    character_id = await _create_character(
        db, owner, member, human_race_id, fighter_class_id
    )
    service = CharacterService()
    await service.update_character(
        character_id, owner.id, CharacterUpdate(hit_point_current=0), db
    )
    await service.death_save(
        character_id, owner.id, CharacterDeathSaveRequest(manual_roll=5), db
    )

    character = await service.update_character(
        character_id, owner.id, CharacterUpdate(hit_point_current=3), db
    )
    assert character.death_save_successes == 0
    assert character.death_save_failures == 0


async def test_cast_concentration_spell_sets_concentrating_spell(
    db: AsyncSession, human_race_id: str, sorcerer_class_id: str
) -> None:
    """Casting a concentration spell records it as the active concentration."""
    owner = await _make_user(db, email="player@example.com")
    member = await _make_membership(db, owner)
    character_id = await _create_character(
        db, owner, member, human_race_id, sorcerer_class_id
    )
    spell_id = await _spell_id_for_class(
        db, sorcerer_class_id, level=1, concentration=True
    )
    service = CharacterService()
    character = await service.add_spell(
        character_id,
        owner.id,
        CharacterSpellCreate(spell_id=uuid.UUID(spell_id), source_class="sorcerer"),
        db,
    )
    entry_id = character.spells[0].id

    character = (
        await service.cast_spell(
            character_id, entry_id, owner.id, CharacterSpellCastRequest(), db
        )
    ).character
    assert character.concentrating_spell_id == uuid.UUID(spell_id)


async def test_cast_second_concentration_spell_replaces_first(
    db: AsyncSession, human_race_id: str, sorcerer_class_id: str
) -> None:
    """Casting a new concentration spell drops whatever was concentrated before."""
    owner = await _make_user(db, email="player@example.com")
    member = await _make_membership(db, owner)
    character_id = await _create_character(
        db, owner, member, human_race_id, sorcerer_class_id, level=3
    )
    service = CharacterService()
    result = await db.execute(
        select(Spell.id)
        .join(SpellClass, SpellClass.spell_id == Spell.id)
        .where(
            SpellClass.class_definition_id == uuid.UUID(sorcerer_class_id),
            Spell.level == 1,
            Spell.concentration.is_(True),
        )
        .limit(2)
    )
    spell_ids = [str(row) for row in result.scalars().all()]
    assert len(spell_ids) >= 2

    for spell_id in spell_ids:
        character = await service.add_spell(
            character_id,
            owner.id,
            CharacterSpellCreate(spell_id=uuid.UUID(spell_id), source_class="sorcerer"),
            db,
        )
    entry_by_spell = {str(s.spell_id): s.id for s in character.spells}

    character = (
        await service.cast_spell(
            character_id,
            entry_by_spell[spell_ids[0]],
            owner.id,
            CharacterSpellCastRequest(),
            db,
        )
    ).character
    assert character.concentrating_spell_id == uuid.UUID(spell_ids[0])

    character = (
        await service.cast_spell(
            character_id,
            entry_by_spell[spell_ids[1]],
            owner.id,
            CharacterSpellCastRequest(),
            db,
        )
    ).character
    assert character.concentrating_spell_id == uuid.UUID(spell_ids[1])


async def test_set_concentration_end_clears_it(
    db: AsyncSession, human_race_id: str, sorcerer_class_id: str
) -> None:
    """Ending concentration explicitly clears `concentrating_spell_id`."""
    owner = await _make_user(db, email="player@example.com")
    member = await _make_membership(db, owner)
    character_id = await _create_character(
        db, owner, member, human_race_id, sorcerer_class_id
    )
    spell_id = await _spell_id_for_class(
        db, sorcerer_class_id, level=1, concentration=True
    )
    service = CharacterService()
    character = await service.add_spell(
        character_id,
        owner.id,
        CharacterSpellCreate(spell_id=uuid.UUID(spell_id), source_class="sorcerer"),
        db,
    )
    entry_id = character.spells[0].id
    await service.cast_spell(
        character_id, entry_id, owner.id, CharacterSpellCastRequest(), db
    )

    character = await service.set_concentration(
        character_id, owner.id, CharacterConcentrationRequest(spell_id=None), db
    )
    assert character.concentrating_spell_id is None


async def test_set_concentration_non_concentration_spell_rejected(
    db: AsyncSession, human_race_id: str, sorcerer_class_id: str
) -> None:
    """Starting concentration on a spell that doesn't require it is a 422."""
    owner = await _make_user(db, email="player@example.com")
    member = await _make_membership(db, owner)
    character_id = await _create_character(
        db, owner, member, human_race_id, sorcerer_class_id
    )
    spell_id = await _spell_id_for_class(
        db, sorcerer_class_id, level=1, concentration=False
    )
    service = CharacterService()
    character = await service.add_spell(
        character_id,
        owner.id,
        CharacterSpellCreate(spell_id=uuid.UUID(spell_id), source_class="sorcerer"),
        db,
    )

    with pytest.raises(HTTPException) as exc:
        await service.set_concentration(
            character_id,
            owner.id,
            CharacterConcentrationRequest(spell_id=uuid.UUID(spell_id)),
            db,
        )
    assert exc.value.status_code == 422


async def test_passive_perception_defaults_to_ten_plus_bonus(
    db: AsyncSession, human_race_id: str, fighter_class_id: str
) -> None:
    """Passive skills default to `10 + bonus` with no proficiency."""
    owner = await _make_user(db, email="player@example.com")
    member = await _make_membership(db, owner)
    character_id = await _create_character(
        db, owner, member, human_race_id, fighter_class_id
    )
    service = CharacterService()
    character = await service.get_character(character_id, owner.id, db)

    # WIS 10 -> +0 modifier; INT 12 -> +1 modifier; no proficiency.
    assert character.passive_perception == 10
    assert character.passive_investigation == 11
    assert character.passive_insight == 10


async def test_passive_perception_reflects_proficiency(
    db: AsyncSession, human_race_id: str, fighter_class_id: str
) -> None:
    """Passive Perception adds the skill's proficiency bonus when proficient."""
    owner = await _make_user(db, email="player@example.com")
    member = await _make_membership(db, owner)
    character_id = await _create_character(
        db, owner, member, human_race_id, fighter_class_id
    )
    result = await db.execute(
        select(CharacterSkill).where(
            CharacterSkill.character_id == character_id,
            CharacterSkill.skill == Skill.perception,
        )
    )
    skill = result.scalar_one()
    skill.proficient = True
    await db.commit()

    service = CharacterService()
    character = await service.get_character(character_id, owner.id, db)

    # WIS 10 -> +0 modifier; level 1 proficiency bonus +2.
    assert character.passive_perception == 12
    # INT 12 -> +1 modifier; unaffected by Perception's proficiency.
    assert character.passive_investigation == 11


async def test_level_up_increases_hp_and_proficiency_bonus(
    db: AsyncSession, human_race_id: str, fighter_class_id: str
) -> None:
    """Leveling up rolls (or takes manual) HP and recalculates derived fields."""
    owner = await _make_user(db, email="player@example.com")
    member = await _make_membership(db, owner)
    character_id = await _create_character(
        db, owner, member, human_race_id, fighter_class_id
    )
    service = CharacterService()
    before = await service.get_character(character_id, owner.id, db)
    assert before.hit_point_max == 11  # d10 + CON +1

    character = await service.level_up(
        character_id,
        owner.id,
        CharacterLevelUpRequest(
            class_definition_id=uuid.UUID(fighter_class_id), manual_hit_die_roll=6
        ),
        db,
    )
    assert character.level == 2
    assert character.classes[0].level == 2
    assert character.hit_point_max == 18  # 11 + (6 + CON +1)
    assert character.hit_point_current == 18
    assert character.proficiency_bonus == 2  # still +2 at level 2


async def test_level_up_at_asi_level_accepts_ability_score_increases(
    db: AsyncSession, human_race_id: str, fighter_class_id: str
) -> None:
    """An ASI level accepts a point distribution, raising the ability score."""
    owner = await _make_user(db, email="player@example.com")
    member = await _make_membership(db, owner)
    character_id = await _create_character(
        db, owner, member, human_race_id, fighter_class_id
    )
    service = CharacterService()
    for level in (2, 3, 4):
        character = await service.level_up(
            character_id,
            owner.id,
            CharacterLevelUpRequest(
                class_definition_id=uuid.UUID(fighter_class_id),
                manual_hit_die_roll=6,
                ability_score_increases=({AbilityScore.str: 2} if level == 4 else None),
            ),
            db,
        )
    assert character.level == 4
    str_score = next(
        s for s in character.ability_scores if s.ability == AbilityScore.str
    )
    assert str_score.asi_bonus == 2
    assert str_score.modifier == 3  # STR 15 + 2 = 17 -> +3


async def test_level_up_ability_score_increases_and_feat_mutually_exclusive(
    db: AsyncSession, human_race_id: str, fighter_class_id: str
) -> None:
    """Supplying both ability_score_increases and feat_id is a 422."""
    owner = await _make_user(db, email="player@example.com")
    member = await _make_membership(db, owner)
    character_id = await _create_character(
        db, owner, member, human_race_id, fighter_class_id
    )
    service = CharacterService()
    feat_result = await db.execute(select(Feat).where(Feat.index == "grappler"))
    feat = feat_result.scalar_one()

    with pytest.raises(HTTPException) as exc:
        await service.level_up(
            character_id,
            owner.id,
            CharacterLevelUpRequest(
                class_definition_id=uuid.UUID(fighter_class_id),
                ability_score_increases={AbilityScore.str: 2},
                feat_id=feat.id,
            ),
            db,
        )
    assert exc.value.status_code == 422


async def test_level_up_asi_not_at_asi_level_rejected(
    db: AsyncSession, human_race_id: str, fighter_class_id: str
) -> None:
    """Requesting an ASI at a level that doesn't grant one is a 422."""
    owner = await _make_user(db, email="player@example.com")
    member = await _make_membership(db, owner)
    character_id = await _create_character(
        db, owner, member, human_race_id, fighter_class_id
    )
    service = CharacterService()

    with pytest.raises(HTTPException) as exc:
        await service.level_up(
            character_id,
            owner.id,
            CharacterLevelUpRequest(
                class_definition_id=uuid.UUID(fighter_class_id),
                ability_score_increases={AbilityScore.str: 2},
            ),
            db,
        )
    assert exc.value.status_code == 422


async def test_level_up_feat_with_unmet_prerequisite_rejected(
    db: AsyncSession, human_race_id: str, fighter_class_id: str
) -> None:
    """A feat whose ability score prerequisite isn't met is a 422."""
    owner = await _make_user(db, email="player@example.com")
    member = await _make_membership(db, owner)
    service = CharacterService()
    character = await service.create_character(
        owner.id,
        CharacterCreate(
            campaign_member_id=member.id,
            name="Weak",
            race_id=uuid.UUID(human_race_id),
            ability_scores=[
                CharacterAbilityScoreCreate(ability=ability, base_score=score)
                for ability, score in {
                    **_STANDARD_ARRAY,
                    AbilityScore.str: 10,
                }.items()
            ],
            classes=[
                CharacterClassCreate(class_definition_id=uuid.UUID(fighter_class_id))
            ],
        ),
        db,
    )
    feat_result = await db.execute(select(Feat).where(Feat.index == "grappler"))
    feat = feat_result.scalar_one()

    for level in (2, 3):
        await service.level_up(
            character.id,
            owner.id,
            CharacterLevelUpRequest(
                class_definition_id=uuid.UUID(fighter_class_id),
                manual_hit_die_roll=6,
            ),
            db,
        )
    with pytest.raises(HTTPException) as exc:
        await service.level_up(
            character.id,
            owner.id,
            CharacterLevelUpRequest(
                class_definition_id=uuid.UUID(fighter_class_id),
                manual_hit_die_roll=6,
                feat_id=feat.id,
            ),
            db,
        )
    assert exc.value.status_code == 422


async def test_level_up_feat_records_character_feature(
    db: AsyncSession, human_race_id: str, fighter_class_id: str
) -> None:
    """Choosing a feat whose prerequisites are met records it as a feature."""
    owner = await _make_user(db, email="player@example.com")
    member = await _make_membership(db, owner)
    character_id = await _create_character(
        db, owner, member, human_race_id, fighter_class_id
    )
    service = CharacterService()
    feat_result = await db.execute(select(Feat).where(Feat.index == "grappler"))
    feat = feat_result.scalar_one()

    for level in (2, 3, 4):
        character = await service.level_up(
            character_id,
            owner.id,
            CharacterLevelUpRequest(
                class_definition_id=uuid.UUID(fighter_class_id),
                manual_hit_die_roll=6,
                feat_id=feat.id if level == 4 else None,
            ),
            db,
        )
    assert any(f.feature_name.lower() == "grappler" for f in character.features)


async def _fighting_style_option_id(db: AsyncSession, index: str) -> uuid.UUID:
    """Return the id of one of Ranger's Fighting Style options, by index."""
    result = await db.execute(select(Feature).where(Feature.index == index))
    return result.scalar_one().id


async def test_level_up_choice_feature_without_feature_choices_rejected(
    db: AsyncSession, human_race_id: str, ranger_class_id: str
) -> None:
    """Leveling into a choice feature (Fighting Style) with no pick is a 422."""
    owner = await _make_user(db, email="player@example.com")
    member = await _make_membership(db, owner)
    character_id = await _create_character(
        db, owner, member, human_race_id, ranger_class_id
    )
    service = CharacterService()

    with pytest.raises(HTTPException) as exc:
        await service.level_up(
            character_id,
            owner.id,
            CharacterLevelUpRequest(
                class_definition_id=uuid.UUID(ranger_class_id), manual_hit_die_roll=6
            ),
            db,
        )
    assert exc.value.status_code == 422
    assert isinstance(exc.value.detail, dict)
    assert exc.value.detail["requires_choice"] is True
    assert exc.value.detail["choices"][0]["options"]


async def test_level_up_choice_feature_invalid_option_rejected(
    db: AsyncSession, human_race_id: str, ranger_class_id: str
) -> None:
    """An option that doesn't belong to the granted feature is rejected."""
    owner = await _make_user(db, email="player@example.com")
    member = await _make_membership(db, owner)
    character_id = await _create_character(
        db, owner, member, human_race_id, ranger_class_id
    )
    service = CharacterService()
    fighting_style_result = await db.execute(
        select(Feature).where(Feature.index == "ranger-fighting-style")
    )
    fighting_style_id = fighting_style_result.scalar_one().id

    with pytest.raises(HTTPException) as exc:
        await service.level_up(
            character_id,
            owner.id,
            CharacterLevelUpRequest(
                class_definition_id=uuid.UUID(ranger_class_id),
                manual_hit_die_roll=6,
                feature_choices=[
                    CharacterFeatureChoiceInput(
                        feature_id=fighting_style_id,
                        feature_option_id=uuid.uuid4(),
                    )
                ],
            ),
            db,
        )
    assert exc.value.status_code == 422


async def test_level_up_choice_feature_persists_and_appears_on_read(
    db: AsyncSession, human_race_id: str, ranger_class_id: str
) -> None:
    """A valid choice is persisted and shows up on the character's sheet."""
    owner = await _make_user(db, email="player@example.com")
    member = await _make_membership(db, owner)
    character_id = await _create_character(
        db, owner, member, human_race_id, ranger_class_id
    )
    service = CharacterService()
    fighting_style_result = await db.execute(
        select(Feature).where(Feature.index == "ranger-fighting-style")
    )
    fighting_style_id = fighting_style_result.scalar_one().id
    archery_id = await _fighting_style_option_id(db, "ranger-fighting-style-archery")

    character = await service.level_up(
        character_id,
        owner.id,
        CharacterLevelUpRequest(
            class_definition_id=uuid.UUID(ranger_class_id),
            manual_hit_die_roll=6,
            feature_choices=[
                CharacterFeatureChoiceInput(
                    feature_id=fighting_style_id, feature_option_id=archery_id
                )
            ],
        ),
        db,
    )

    assert character.level == 2
    assert len(character.feature_choices) == 1
    assert character.feature_choices[0].feature_id == fighting_style_id
    assert character.feature_choices[0].feature_option_id == archery_id


async def test_level_up_without_choice_feature_requires_nothing(
    db: AsyncSession, human_race_id: str, fighter_class_id: str
) -> None:
    """A level that grants no choice feature never requires `feature_choices`."""
    owner = await _make_user(db, email="player@example.com")
    member = await _make_membership(db, owner)
    character_id = await _create_character(
        db, owner, member, human_race_id, fighter_class_id
    )
    service = CharacterService()

    # Fighter's Fighting Style is granted at level 1 (already at creation) —
    # leveling to 2 grants nothing that needs a choice.
    character = await service.level_up(
        character_id,
        owner.id,
        CharacterLevelUpRequest(
            class_definition_id=uuid.UUID(fighter_class_id), manual_hit_die_roll=6
        ),
        db,
    )
    assert character.level == 2
    assert character.feature_choices == []


async def _eldritch_invocation_ids(db: AsyncSession, count: int) -> list[uuid.UUID]:
    result = await db.execute(
        select(Feature.id)
        .where(Feature.index.like("eldritch-invocation-%"))
        .order_by(Feature.index)
        .limit(count)
    )
    return list(result.scalars().all())


async def test_level_up_multi_choice_feature_requires_correct_count(
    db: AsyncSession, human_race_id: str, warlock_class_id: str
) -> None:
    """Eldritch Invocations grants 2 picks at level 2 — 1 pick isn't enough."""
    owner = await _make_user(db, email="player@example.com")
    member = await _make_membership(db, owner)
    character_id = await _create_character(
        db, owner, member, human_race_id, warlock_class_id
    )
    invocations_feature = (
        await db.execute(select(Feature).where(Feature.index == "eldritch-invocations"))
    ).scalar_one()
    option_ids = await _eldritch_invocation_ids(db, 1)
    service = CharacterService()

    with pytest.raises(HTTPException) as exc:
        await service.level_up(
            character_id,
            owner.id,
            CharacterLevelUpRequest(
                class_definition_id=uuid.UUID(warlock_class_id),
                manual_hit_die_roll=6,
                feature_choices=[
                    CharacterFeatureChoiceInput(
                        feature_id=invocations_feature.id,
                        feature_option_id=option_ids[0],
                    )
                ],
            ),
            db,
        )
    assert exc.value.status_code == 422
    assert isinstance(exc.value.detail, dict)
    choice_detail = exc.value.detail["choices"][0]
    assert choice_detail["required_count"] == 2


async def test_level_up_multi_choice_feature_persists_all_picks(
    db: AsyncSession, human_race_id: str, warlock_class_id: str
) -> None:
    """2 distinct picks for Eldritch Invocations both persist."""
    owner = await _make_user(db, email="player@example.com")
    member = await _make_membership(db, owner)
    character_id = await _create_character(
        db, owner, member, human_race_id, warlock_class_id
    )
    invocations_feature = (
        await db.execute(select(Feature).where(Feature.index == "eldritch-invocations"))
    ).scalar_one()
    option_ids = await _eldritch_invocation_ids(db, 2)
    service = CharacterService()

    character = await service.level_up(
        character_id,
        owner.id,
        CharacterLevelUpRequest(
            class_definition_id=uuid.UUID(warlock_class_id),
            manual_hit_die_roll=6,
            feature_choices=[
                CharacterFeatureChoiceInput(
                    feature_id=invocations_feature.id, feature_option_id=option_ids[0]
                ),
                CharacterFeatureChoiceInput(
                    feature_id=invocations_feature.id, feature_option_id=option_ids[1]
                ),
            ],
        ),
        db,
    )

    persisted_option_ids = {c.feature_option_id for c in character.feature_choices}
    assert persisted_option_ids == set(option_ids)


async def test_level_up_multi_choice_feature_rejects_duplicate_pick(
    db: AsyncSession, human_race_id: str, warlock_class_id: str
) -> None:
    """Picking the same Eldritch Invocation option twice in one request is rejected."""
    owner = await _make_user(db, email="player@example.com")
    member = await _make_membership(db, owner)
    character_id = await _create_character(
        db, owner, member, human_race_id, warlock_class_id
    )
    invocations_feature = (
        await db.execute(select(Feature).where(Feature.index == "eldritch-invocations"))
    ).scalar_one()
    option_ids = await _eldritch_invocation_ids(db, 1)
    service = CharacterService()

    with pytest.raises(HTTPException) as exc:
        await service.level_up(
            character_id,
            owner.id,
            CharacterLevelUpRequest(
                class_definition_id=uuid.UUID(warlock_class_id),
                manual_hit_die_roll=6,
                feature_choices=[
                    CharacterFeatureChoiceInput(
                        feature_id=invocations_feature.id,
                        feature_option_id=option_ids[0],
                    ),
                    CharacterFeatureChoiceInput(
                        feature_id=invocations_feature.id,
                        feature_option_id=option_ids[0],
                    ),
                ],
            ),
            db,
        )
    assert exc.value.status_code == 422


async def _create_druid_of_the_land(
    db: AsyncSession,
    owner: User,
    member: CampaignMember,
    human_race_id: str,
    druid_class_id: str,
    druid_land_subclass_id: str,
) -> uuid.UUID:
    service = CharacterService()
    character = await service.create_character(
        owner.id,
        CharacterCreate(
            campaign_member_id=member.id,
            name="Thornwood",
            race_id=uuid.UUID(human_race_id),
            ability_scores=_ability_scores(),
            classes=[
                CharacterClassCreate(
                    class_definition_id=uuid.UUID(druid_class_id),
                    subclass_id=uuid.UUID(druid_land_subclass_id),
                )
            ],
        ),
        db,
    )
    return character.id


async def test_level_up_subclass_choice_feature_requires_pick(
    db: AsyncSession,
    human_race_id: str,
    druid_class_id: str,
    druid_land_subclass_id: str,
) -> None:
    """Circle of the Land (a subclass feature) requires a terrain pick at level 2."""
    owner = await _make_user(db, email="player@example.com")
    member = await _make_membership(db, owner)
    character_id = await _create_druid_of_the_land(
        db, owner, member, human_race_id, druid_class_id, druid_land_subclass_id
    )
    service = CharacterService()

    with pytest.raises(HTTPException) as exc:
        await service.level_up(
            character_id,
            owner.id,
            CharacterLevelUpRequest(
                class_definition_id=uuid.UUID(druid_class_id), manual_hit_die_roll=6
            ),
            db,
        )
    assert exc.value.status_code == 422


async def test_level_up_subclass_choice_feature_persists_pick(
    db: AsyncSession,
    human_race_id: str,
    druid_class_id: str,
    druid_land_subclass_id: str,
) -> None:
    """A valid Circle of the Land terrain pick persists and shows up on the sheet."""
    owner = await _make_user(db, email="player@example.com")
    member = await _make_membership(db, owner)
    character_id = await _create_druid_of_the_land(
        db, owner, member, human_race_id, druid_class_id, druid_land_subclass_id
    )
    service = CharacterService()
    circle_feature = (
        await db.execute(select(Feature).where(Feature.index == "circle-of-the-land"))
    ).scalar_one()
    arctic_result = await db.execute(
        select(Feature).where(Feature.index == "circle-of-the-land-arctic")
    )
    arctic_id = arctic_result.scalar_one().id

    leveled = await service.level_up(
        character_id,
        owner.id,
        CharacterLevelUpRequest(
            class_definition_id=uuid.UUID(druid_class_id),
            manual_hit_die_roll=6,
            feature_choices=[
                CharacterFeatureChoiceInput(
                    feature_id=circle_feature.id, feature_option_id=arctic_id
                )
            ],
        ),
        db,
    )
    assert leveled.feature_choices[0].feature_option_id == arctic_id


async def test_use_resource_consumes_and_rejects_past_limit(
    db: AsyncSession, human_race_id: str, barbarian_class_id: str
) -> None:
    """Using a resource consumes it, and rejects once at its limit."""
    owner = await _make_user(db, email="player@example.com")
    member = await _make_membership(db, owner)
    character_id = await _create_character(
        db, owner, member, human_race_id, barbarian_class_id
    )
    service = CharacterService()

    character = await service.use_resource(character_id, owner.id, "rage_count", db)
    resource = next(r for r in character.resources if r.resource_key == "rage_count")
    assert resource.used == 1
    assert resource.max == 2  # level 1 Barbarian

    character = await service.use_resource(character_id, owner.id, "rage_count", db)
    resource = next(r for r in character.resources if r.resource_key == "rage_count")
    assert resource.used == 2

    with pytest.raises(HTTPException) as exc:
        await service.use_resource(character_id, owner.id, "rage_count", db)
    assert exc.value.status_code == 422


async def _create_cleric_of_life(
    db: AsyncSession,
    owner: User,
    member: CampaignMember,
    human_race_id: str,
    cleric_class_id: str,
    cleric_life_subclass_id: str,
) -> uuid.UUID:
    """Create a level-2 Cleric of the Life domain (has Channel Divinity)."""
    service = CharacterService()
    character = await service.create_character(
        owner.id,
        CharacterCreate(
            campaign_member_id=member.id,
            name="Priestess",
            race_id=uuid.UUID(human_race_id),
            ability_scores=_ability_scores(),
            classes=[
                CharacterClassCreate(
                    class_definition_id=uuid.UUID(cleric_class_id),
                    subclass_id=uuid.UUID(cleric_life_subclass_id),
                    level=2,
                )
            ],
        ),
        db,
    )
    return character.id


async def test_get_resource_options_lists_channel_divinity_choices(
    db: AsyncSession,
    human_race_id: str,
    cleric_class_id: str,
    cleric_life_subclass_id: str,
) -> None:
    """A Life Cleric's Channel Divinity options are listed by name (Fase 8)."""
    owner = await _make_user(db, email="player@example.com")
    member = await _make_membership(db, owner)
    character_id = await _create_cleric_of_life(
        db, owner, member, human_race_id, cleric_class_id, cleric_life_subclass_id
    )
    service = CharacterService()

    options = await service.get_resource_options(
        character_id, owner.id, "channel_divinity_charges", db
    )

    assert len(options) == 2
    assert {o.index for o in options} == {
        "channel-divinity-turn-undead",
        "channel-divinity-preserve-life",
    }


async def test_get_resource_options_empty_for_resource_without_options(
    db: AsyncSession, human_race_id: str, barbarian_class_id: str
) -> None:
    """A resource without an option concept (rage) lists no options."""
    owner = await _make_user(db, email="player@example.com")
    member = await _make_membership(db, owner)
    character_id = await _create_character(
        db, owner, member, human_race_id, barbarian_class_id
    )
    service = CharacterService()

    options = await service.get_resource_options(
        character_id, owner.id, "rage_count", db
    )

    assert options == []


async def test_use_resource_multiple_options_requires_option_id(
    db: AsyncSession,
    human_race_id: str,
    cleric_class_id: str,
    cleric_life_subclass_id: str,
) -> None:
    """A Life Cleric has 2 Channel Divinity options — using it needs option_id."""
    owner = await _make_user(db, email="player@example.com")
    member = await _make_membership(db, owner)
    character_id = await _create_cleric_of_life(
        db, owner, member, human_race_id, cleric_class_id, cleric_life_subclass_id
    )
    service = CharacterService()

    with pytest.raises(HTTPException) as exc:
        await service.use_resource(
            character_id, owner.id, "channel_divinity_charges", db
        )
    assert exc.value.status_code == 422


async def test_use_resource_records_which_option_was_spent(
    db: AsyncSession,
    human_race_id: str,
    cleric_class_id: str,
    cleric_life_subclass_id: str,
) -> None:
    """A valid option_id is recorded on the resource entry."""
    owner = await _make_user(db, email="player@example.com")
    member = await _make_membership(db, owner)
    character_id = await _create_cleric_of_life(
        db, owner, member, human_race_id, cleric_class_id, cleric_life_subclass_id
    )
    service = CharacterService()
    preserve_life_result = await db.execute(
        select(Feature).where(Feature.index == "channel-divinity-preserve-life")
    )
    preserve_life_id = preserve_life_result.scalar_one().id

    character = await service.use_resource(
        character_id,
        owner.id,
        "channel_divinity_charges",
        db,
        option_id=preserve_life_id,
    )

    resource = next(
        r for r in character.resources if r.resource_key == "channel_divinity_charges"
    )
    assert resource.used == 1
    assert resource.last_feature_option_id == preserve_life_id


async def test_use_resource_invalid_option_rejected(
    db: AsyncSession,
    human_race_id: str,
    cleric_class_id: str,
    cleric_life_subclass_id: str,
) -> None:
    """An option_id that isn't one of the character's options is rejected."""
    owner = await _make_user(db, email="player@example.com")
    member = await _make_membership(db, owner)
    character_id = await _create_cleric_of_life(
        db, owner, member, human_race_id, cleric_class_id, cleric_life_subclass_id
    )
    service = CharacterService()

    with pytest.raises(HTTPException) as exc:
        await service.use_resource(
            character_id,
            owner.id,
            "channel_divinity_charges",
            db,
            option_id=uuid.uuid4(),
        )
    assert exc.value.status_code == 422


async def test_use_resource_single_option_does_not_require_option_id(
    db: AsyncSession, human_race_id: str, barbarian_class_id: str
) -> None:
    """A resource with no option concept (rage) never requires option_id."""
    owner = await _make_user(db, email="player@example.com")
    member = await _make_membership(db, owner)
    character_id = await _create_character(
        db, owner, member, human_race_id, barbarian_class_id
    )
    service = CharacterService()

    character = await service.use_resource(character_id, owner.id, "rage_count", db)
    resource = next(r for r in character.resources if r.resource_key == "rage_count")
    assert resource.used == 1
    assert resource.last_feature_option_id is None


async def test_use_resource_untrackable_key_rejected(
    db: AsyncSession, human_race_id: str, barbarian_class_id: str
) -> None:
    """A resource_key outside `_RESOURCE_RECHARGE` is rejected."""
    owner = await _make_user(db, email="player@example.com")
    member = await _make_membership(db, owner)
    character_id = await _create_character(
        db, owner, member, human_race_id, barbarian_class_id
    )
    service = CharacterService()

    with pytest.raises(HTTPException) as exc:
        await service.use_resource(character_id, owner.id, "brutal_critical_dice", db)
    assert exc.value.status_code == 422


async def test_use_resource_character_class_does_not_grant_it_rejected(
    db: AsyncSession, human_race_id: str, fighter_class_id: str
) -> None:
    """A resource no class of the character grants is rejected."""
    owner = await _make_user(db, email="player@example.com")
    member = await _make_membership(db, owner)
    character_id = await _create_character(
        db, owner, member, human_race_id, fighter_class_id
    )
    service = CharacterService()

    with pytest.raises(HTTPException) as exc:
        await service.use_resource(character_id, owner.id, "rage_count", db)
    assert exc.value.status_code == 422


async def test_long_rest_restores_resources(
    db: AsyncSession, human_race_id: str, barbarian_class_id: str
) -> None:
    """A long rest restores a long-recharge resource (rage)."""
    owner = await _make_user(db, email="player@example.com")
    member = await _make_membership(db, owner)
    character_id = await _create_character(
        db, owner, member, human_race_id, barbarian_class_id
    )
    service = CharacterService()
    await service.use_resource(character_id, owner.id, "rage_count", db)
    await service.use_resource(character_id, owner.id, "rage_count", db)

    character = (await service.rest(
        character_id, owner.id, CharacterRestRequest(rest_type="long"), db
    )).character
    resource = next(r for r in character.resources if r.resource_key == "rage_count")
    assert resource.used == 0


async def test_short_rest_does_not_restore_long_recharge_resource(
    db: AsyncSession, human_race_id: str, barbarian_class_id: str
) -> None:
    """A short rest doesn't restore a long-recharge resource (rage)."""
    owner = await _make_user(db, email="player@example.com")
    member = await _make_membership(db, owner)
    character_id = await _create_character(
        db, owner, member, human_race_id, barbarian_class_id
    )
    service = CharacterService()
    await service.use_resource(character_id, owner.id, "rage_count", db)

    character = (await service.rest(
        character_id, owner.id, CharacterRestRequest(rest_type="short"), db
    )).character
    resource = next(r for r in character.resources if r.resource_key == "rage_count")
    assert resource.used == 1


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


async def test_equip_light_armor_recalculates_ac_with_full_dex(
    db: AsyncSession,
    human_race_id: str,
    fighter_class_id: str,
    leather_armor_item_id: str,
) -> None:
    """Equipping light armor adds the full DEX modifier."""
    owner = await _make_user(db, email="player@example.com")
    member = await _make_membership(db, owner)
    character_id = await _create_character(
        db, owner, member, human_race_id, fighter_class_id
    )
    service = CharacterService()
    character = await service.add_equipment(
        character_id,
        owner.id,
        CharacterEquipmentCreate(item_id=uuid.UUID(leather_armor_item_id)),
        db,
    )
    entry_id = character.equipment[0].id

    character = await service.update_equipment(
        character_id, entry_id, owner.id, CharacterEquipmentUpdate(equipped=True), db
    )

    # Leather Armor base 11 + DEX 14 (+2 mod), no cap.
    assert character.armor_class == 13


async def test_equip_medium_armor_caps_dex_bonus(
    db: AsyncSession,
    human_race_id: str,
    fighter_class_id: str,
    breastplate_item_id: str,
) -> None:
    """Equipping medium armor caps the DEX modifier at its `dex_bonus_cap`."""
    owner = await _make_user(db, email="player@example.com")
    member = await _make_membership(db, owner)
    character_id = await _create_character(
        db, owner, member, human_race_id, fighter_class_id
    )
    service = CharacterService()
    character = await service.add_equipment(
        character_id,
        owner.id,
        CharacterEquipmentCreate(item_id=uuid.UUID(breastplate_item_id)),
        db,
    )
    entry_id = character.equipment[0].id

    character = await service.update_equipment(
        character_id, entry_id, owner.id, CharacterEquipmentUpdate(equipped=True), db
    )

    # Breastplate base 14 + DEX 14 (+2 mod, within the +2 cap).
    assert character.armor_class == 16


async def test_equip_heavy_armor_ignores_dex(
    db: AsyncSession, human_race_id: str, fighter_class_id: str, chain_mail_item_id: str
) -> None:
    """Equipping heavy armor never adds the DEX modifier."""
    owner = await _make_user(db, email="player@example.com")
    member = await _make_membership(db, owner)
    character_id = await _create_character(
        db, owner, member, human_race_id, fighter_class_id
    )
    service = CharacterService()
    character = await service.add_equipment(
        character_id,
        owner.id,
        CharacterEquipmentCreate(item_id=uuid.UUID(chain_mail_item_id)),
        db,
    )
    entry_id = character.equipment[0].id

    character = await service.update_equipment(
        character_id, entry_id, owner.id, CharacterEquipmentUpdate(equipped=True), db
    )

    # Chain Mail base 16, DEX never applies.
    assert character.armor_class == 16


async def test_equip_shield_adds_flat_bonus(
    db: AsyncSession, human_race_id: str, fighter_class_id: str, shield_item_id: str
) -> None:
    """Equipping a shield adds its base_ac on top of the unarmored/armor AC."""
    owner = await _make_user(db, email="player@example.com")
    member = await _make_membership(db, owner)
    character_id = await _create_character(
        db, owner, member, human_race_id, fighter_class_id
    )
    service = CharacterService()
    character = await service.add_equipment(
        character_id,
        owner.id,
        CharacterEquipmentCreate(item_id=uuid.UUID(shield_item_id)),
        db,
    )
    entry_id = character.equipment[0].id

    character = await service.update_equipment(
        character_id, entry_id, owner.id, CharacterEquipmentUpdate(equipped=True), db
    )

    # Unarmored 10 + DEX 14 (+2 mod) + Shield 2.
    assert character.armor_class == 14


async def test_unequip_armor_recalculates_ac_without_it(
    db: AsyncSession,
    human_race_id: str,
    fighter_class_id: str,
    leather_armor_item_id: str,
) -> None:
    """Unequipping armor recomputes AC back to the unarmored value."""
    owner = await _make_user(db, email="player@example.com")
    member = await _make_membership(db, owner)
    character_id = await _create_character(
        db, owner, member, human_race_id, fighter_class_id
    )
    service = CharacterService()
    character = await service.add_equipment(
        character_id,
        owner.id,
        CharacterEquipmentCreate(item_id=uuid.UUID(leather_armor_item_id)),
        db,
    )
    entry_id = character.equipment[0].id
    await service.update_equipment(
        character_id, entry_id, owner.id, CharacterEquipmentUpdate(equipped=True), db
    )

    character = await service.update_equipment(
        character_id, entry_id, owner.id, CharacterEquipmentUpdate(equipped=False), db
    )

    # Back to unarmored 10 + DEX 14 (+2 mod).
    assert character.armor_class == 12


async def test_manual_armor_class_override_survives_until_next_toggle(
    db: AsyncSession,
    human_race_id: str,
    fighter_class_id: str,
    leather_armor_item_id: str,
) -> None:
    """A manual PATCH override holds until the next equip/unequip toggle."""
    owner = await _make_user(db, email="player@example.com")
    member = await _make_membership(db, owner)
    character_id = await _create_character(
        db, owner, member, human_race_id, fighter_class_id
    )
    service = CharacterService()
    character = await service.add_equipment(
        character_id,
        owner.id,
        CharacterEquipmentCreate(item_id=uuid.UUID(leather_armor_item_id)),
        db,
    )
    entry_id = character.equipment[0].id
    await service.update_equipment(
        character_id, entry_id, owner.id, CharacterEquipmentUpdate(equipped=True), db
    )

    character = await service.update_character(
        character_id, owner.id, CharacterUpdate(armor_class=99), db
    )
    assert character.armor_class == 99

    # A quantity-only edit (no equipped toggle) doesn't touch armor_class.
    character = await service.update_equipment(
        character_id, entry_id, owner.id, CharacterEquipmentUpdate(quantity=2), db
    )
    assert character.armor_class == 99

    # Toggling equipped again recomputes it, discarding the override.
    character = await service.update_equipment(
        character_id, entry_id, owner.id, CharacterEquipmentUpdate(equipped=False), db
    )
    assert character.armor_class == 12


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
