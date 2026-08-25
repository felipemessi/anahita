"""CharacterService orchestrates character sheet creation and reads."""

import uuid
from typing import Any, Literal, Protocol

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.campaigns.domain import CampaignRole
from app.campaigns.models import CampaignMember
from app.catalog import service as catalog_service
from app.catalog.domain import AbilityScore, SpellActionType
from app.catalog.models import (
    ClassDefinition,
    ClassLevel,
    ClassLevelResource,
    Feature,
    Spell,
)
from app.characters.domain import (
    MULTICLASS_ABILITY_REQUIREMENTS,
    SKILL_ABILITY,
    CrossCampaignCatalogReferenceError,
    FeatureSourceType,
    InvalidAbilityGenerationError,
    Skill,
    parse_saving_throw_proficiencies,
    validate_ability_generation,
    validate_catalog_reference,
)
from app.characters.models import (
    Character,
    CharacterAbilityScore,
    CharacterClass,
    CharacterEquipment,
    CharacterFeature,
    CharacterFeatureChoice,
    CharacterResource,
    CharacterSkill,
    CharacterSpell,
    CharacterSpellSlot,
)
from app.characters.schemas import (
    CharacterAbilityScoreCreate,
    CharacterAbilityScoreRead,
    CharacterClassCreate,
    CharacterClassRead,
    CharacterCreate,
    CharacterConcentrationRequest,
    CharacterCurrencyRequest,
    CharacterDeathSaveRequest,
    CharacterEquipmentCreate,
    CharacterEquipmentRead,
    CharacterEquipmentUpdate,
    CharacterFeatureChoiceInput,
    CharacterFeatureChoiceRead,
    CharacterFeatureCreate,
    CharacterFeatureRead,
    CharacterHitDiceSpend,
    CharacterLevelUpRequest,
    CharacterRead,
    CharacterResourceRead,
    CharacterRestRequest,
    CharacterSkillRead,
    CharacterSpellCastRequest,
    CharacterSpellCastResponse,
    CharacterSpellCreate,
    CharacterSpellRead,
    CharacterSpellSlotRead,
    CharacterSpellUpdate,
    CharacterSummaryRead,
    CharacterUpdate,
)
from engine.abilities import (
    calculate_modifier,
    calculate_proficiency_bonus,
    calculate_saving_throw_bonus,
    calculate_skill_bonus,
)
from engine import dice
from engine.armor_class import calculate_ac
from engine.hit_points import calculate_max_hp
from engine.spellcasting import (
    KNOWN_CASTER_CLASSES,
    PREPARED_CASTER_CLASSES,
    prepared_spell_limit,
)
from engine.types import Ability as EngineAbility
from engine.validation import validate_multiclass

_CHARACTER_LOAD_OPTIONS = (
    selectinload(Character.ability_scores),
    selectinload(Character.skills),
    selectinload(Character.classes),
    selectinload(Character.spells),
    selectinload(Character.spell_slots),
    selectinload(Character.equipment),
    selectinload(Character.features),
    selectinload(Character.feature_choices),
    selectinload(Character.resources),
)

#: `ClassLevelResource.resource_key` -> which rest type recharges it
#: (Fase 7). `ClassLevelResource` also carries plenty of non-consumable,
#: catalog-only scaling values (`sneak_attack_dice`, `spells_known`,
#: `unarmored_movement`, ...) that a player never "spends" — only the
#: keys listed here are trackable through `CharacterService.use_resource`;
#: everything else 422s. Recharge type isn't itself SRD-structured data in
#: this catalog, so it's hand-mapped from the PHB rather than read from a
#: column.
_RESOURCE_RECHARGE: dict[str, Literal["short", "long"]] = {
    "rage_count": "long",
    "ki_points": "short",
    "sorcery_points": "long",
    "action_surges": "short",
    "channel_divinity_charges": "short",
    "indomitable_uses": "long",
    "bardic_inspiration_die": "long",
}

#: `resource_key` -> the catalog `Feature.index` values that group its named
#: options (Fase 8) — e.g. Cleric's and Paladin's Channel Divinity each have
#: their own parent feature ("channel-divinity-1-rest"/"channel-divinity",
#: see `_CHANNEL_DIVINITY_PARENT_OVERRIDES` in `convert_srd.py`), but both
#: back the same `channel_divinity_charges` resource. A resource_key not
#: listed here has no option concept — `use_resource` never requires or
#: records one for it.
_RESOURCE_OPTION_PARENT_FEATURES: dict[str, tuple[str, ...]] = {
    "channel_divinity_charges": ("channel-divinity-1-rest", "channel-divinity"),
}


class _CatalogScopedEntity(Protocol):
    """Structural type for catalog entities checked by `_validate_reference`."""

    is_custom: bool
    campaign_id: uuid.UUID | None


class CharacterService:
    """Orchestrates character creation, reads, and catalog-reference validation."""

    async def create_character(
        self, requester_id: uuid.UUID, data: CharacterCreate, db: AsyncSession
    ) -> CharacterRead:
        """Create a character sheet tied to `data.campaign_member_id`.

        Only the owner of that campaign membership may create the character.
        Referenced catalog content (race, classes) must be SRD-global or
        homebrew scoped to the membership's own campaign.
        """
        member = await self._require_own_membership(
            data.campaign_member_id, requester_id, db
        )

        scores_by_ability = self._validate_ability_scores(data)
        if data.generation_method is not None:
            try:
                validate_ability_generation(
                    data.generation_method,
                    [score.base_score for score in data.ability_scores],
                )
            except InvalidAbilityGenerationError as exc:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
                ) from exc

        race = await catalog_service.get_race(db, data.race_id)
        if race is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Race not found"
            )
        self._validate_reference(race, member.campaign_id)

        classes = []
        for class_entry in data.classes:
            class_def = await catalog_service.get_class(
                db, class_entry.class_definition_id
            )
            if class_def is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Class {class_entry.class_definition_id} not found",
                )
            self._validate_reference(class_def, member.campaign_id)
            classes.append((class_entry, class_def))

        con_score = scores_by_ability[AbilityScore.con]
        con_mod = calculate_modifier(
            con_score.base_score + con_score.asi_bonus + con_score.misc_bonus
        )
        dex_score = scores_by_ability[AbilityScore.dex]
        dex_mod = calculate_modifier(
            dex_score.base_score + dex_score.asi_bonus + dex_score.misc_bonus
        )
        primary_class_hit_die = classes[0][1].hit_die
        hit_point_max = calculate_max_hp(primary_class_hit_die, data.level, con_mod)
        # Only the starting (first) class grants saving throw proficiencies —
        # multiclassing never adds more (PHB multiclassing rules).
        save_proficiencies = parse_saving_throw_proficiencies(
            classes[0][1].saving_throw_proficiencies
        )

        character = Character(
            campaign_member_id=member.id,
            name=data.name,
            race_id=data.race_id,
            subrace_id=data.subrace_id,
            level=data.level,
            experience_points=data.experience_points,
            alignment=data.alignment,
            background=data.background,
            hit_point_max=hit_point_max,
            hit_point_current=hit_point_max,
            temporary_hit_points=data.temporary_hit_points,
            armor_class=calculate_ac(None, dex_mod),
            speed=race.speed,
            inspiration=data.inspiration,
            proficiency_bonus=calculate_proficiency_bonus(data.level),
            generation_method=data.generation_method,
        )
        db.add(character)
        await db.flush()

        for score in data.ability_scores:
            db.add(
                CharacterAbilityScore(
                    character_id=character.id,
                    ability=score.ability,
                    base_score=score.base_score,
                    asi_bonus=score.asi_bonus,
                    misc_bonus=score.misc_bonus,
                    save_proficient=score.ability in save_proficiencies,
                )
            )
        for class_entry, _class_def in classes:
            db.add(
                CharacterClass(
                    character_id=character.id,
                    class_definition_id=class_entry.class_definition_id,
                    subclass_id=class_entry.subclass_id,
                    level=class_entry.level,
                )
            )
        for skill in Skill:
            db.add(CharacterSkill(character_id=character.id, skill=skill))

        await db.commit()
        return await self._reload_as_read(character.id, db)

    async def get_character(
        self, character_id: uuid.UUID, requester_id: uuid.UUID, db: AsyncSession
    ) -> CharacterRead:
        """Fetch a character with calculated fields (modifiers, skill bonuses).

        Viewable by the character's own player and by the campaign's DM.
        """
        result = await db.execute(
            select(Character)
            .where(Character.id == character_id)
            .options(*_CHARACTER_LOAD_OPTIONS)
        )
        character = result.scalar_one_or_none()
        if character is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Character not found"
            )
        await self._require_viewer(character, requester_id, db)
        spell_catalog = await self._resolve_spell_catalog(character, db)
        max_slots = await self._max_spell_slots(character, db)
        max_resources = await self._max_resources(character, db)
        return self._to_read(character, spell_catalog, max_slots, max_resources)

    async def add_class(
        self,
        character_id: uuid.UUID,
        requester_id: uuid.UUID,
        data: CharacterClassCreate,
        db: AsyncSession,
    ) -> CharacterRead:
        """Add a second (or further) class to a character, enabling multiclass.

        Only the character's own player may do this. The character's current
        ability scores must satisfy the PHB multiclass prerequisites for both
        the class(es) it already has and the class being added.
        """
        result = await db.execute(
            select(Character)
            .where(Character.id == character_id)
            .options(*_CHARACTER_LOAD_OPTIONS)
        )
        character = result.scalar_one_or_none()
        if character is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Character not found"
            )
        member = await self._require_own_membership(
            character.campaign_member_id, requester_id, db
        )

        new_class_def = await catalog_service.get_class(db, data.class_definition_id)
        if new_class_def is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Class not found"
            )
        self._validate_reference(new_class_def, member.campaign_id)

        existing_class_ids = {c.class_definition_id for c in character.classes}
        if data.class_definition_id in existing_class_ids:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Character already has this class; level it up instead",
            )

        if new_class_def.index is not None:
            current_class_indices = await self._current_class_indices(character, db)
            ability_scores = {
                EngineAbility(score.ability.value): (
                    score.base_score + score.asi_bonus + score.misc_bonus
                )
                for score in character.ability_scores
            }
            validation = validate_multiclass(
                current_class_indices,
                new_class_def.index,
                ability_scores,
                MULTICLASS_ABILITY_REQUIREMENTS,
            )
            if not validation.is_valid:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail="; ".join(validation.errors),
                )

        db.add(
            CharacterClass(
                character_id=character.id,
                class_definition_id=data.class_definition_id,
                subclass_id=data.subclass_id,
                level=data.level,
            )
        )
        character.level += data.level
        character.proficiency_bonus = calculate_proficiency_bonus(character.level)

        await db.commit()
        return await self._reload_as_read(character.id, db)

    async def level_up(
        self,
        character_id: uuid.UUID,
        requester_id: uuid.UUID,
        data: CharacterLevelUpRequest,
        db: AsyncSession,
    ) -> CharacterRead:
        """Level up a character by one level in one class. Owner only.

        `class_definition_id` may be a class the character already has
        (leveled up by one) or a new one (multiclassed into at level 1,
        reusing `add_class`'s PHB prerequisite check). Always recalculates
        `hit_point_max`/`hit_point_current` (class hit die + CON modifier)
        and `proficiency_bonus`. At an ASI level (`ClassLevel`'s
        `ability_score_bonuses` set for the new level in this class),
        `ability_score_increases` or `feat_id` may be supplied — see
        `CharacterLevelUpRequest`. If the new level grants a choice feature
        (e.g. Fighting Style, Pact Boon) with no matching `feature_choices`
        entry, nothing is committed and a 422 is raised with
        `requires_choice`/the available options — see
        `_apply_feature_choices`.
        """
        if (
            data.ability_score_increases is not None
            and data.feat_id is not None
        ):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="ability_score_increases and feat_id are mutually exclusive",
            )

        result = await db.execute(
            select(Character)
            .where(Character.id == character_id)
            .options(*_CHARACTER_LOAD_OPTIONS)
        )
        character = result.scalar_one_or_none()
        if character is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Character not found"
            )
        member = await self._require_own_membership(
            character.campaign_member_id, requester_id, db
        )

        class_def = await catalog_service.get_class(db, data.class_definition_id)
        if class_def is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Class not found"
            )
        self._validate_reference(class_def, member.campaign_id)

        class_entry = next(
            (
                c
                for c in character.classes
                if c.class_definition_id == data.class_definition_id
            ),
            None,
        )
        if class_entry is None:
            # New class — multiclassing in, same prerequisite check as
            # `add_class`.
            if class_def.index is not None:
                current_class_indices = await self._current_class_indices(
                    character, db
                )
                ability_scores = {
                    EngineAbility(score.ability.value): (
                        score.base_score + score.asi_bonus + score.misc_bonus
                    )
                    for score in character.ability_scores
                }
                validation = validate_multiclass(
                    current_class_indices,
                    class_def.index,
                    ability_scores,
                    MULTICLASS_ABILITY_REQUIREMENTS,
                )
                if not validation.is_valid:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                        detail="; ".join(validation.errors),
                    )
            class_entry = CharacterClass(
                character_id=character.id,
                class_definition_id=data.class_definition_id,
                subclass_id=data.subclass_id,
                level=0,
            )
            db.add(class_entry)
            new_level_in_class = 1
        else:
            if class_entry.level >= 20:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail="This class is already at level 20",
                )
            new_level_in_class = class_entry.level + 1

        class_entry.level = new_level_in_class
        character.level += 1
        character.proficiency_bonus = calculate_proficiency_bonus(character.level)

        con_mod = self._ability_modifier(character, "con")
        if data.manual_hit_die_roll is not None:
            hp_gained = max(1, data.manual_hit_die_roll + con_mod)
        else:
            hp_gained = max(1, dice.roll(f"1d{class_def.hit_die}").total + con_mod)
        character.hit_point_max += hp_gained
        character.hit_point_current += hp_gained

        class_level_row = self._class_level_row(class_def, new_level_in_class)
        is_asi_level = (
            class_level_row is not None
            and class_level_row.ability_score_bonuses is not None
        )
        wants_asi_or_feat = (
            data.ability_score_increases is not None or data.feat_id is not None
        )
        if wants_asi_or_feat and not is_asi_level:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=(
                    f"Level {new_level_in_class} of {class_def.index} doesn't "
                    "grant an ability score improvement"
                ),
            )

        if data.ability_score_increases is not None:
            await self._apply_ability_score_increases(
                character, data.ability_score_increases
            )
        elif data.feat_id is not None:
            await self._apply_feat_selection(character, data.feat_id, db)

        await self._apply_feature_choices(character, class_level_row, data, db)

        await db.commit()
        return await self._reload_as_read(character.id, db)

    async def _apply_ability_score_increases(
        self, character: Character, increases: dict[AbilityScore, int]
    ) -> None:
        """Apply an ASI's point distribution — up to 2 points, max 2 per ability."""
        total_points = sum(increases.values())
        if total_points != 2 or any(
            points < 0 or points > 2 for points in increases.values()
        ):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=(
                    "ability_score_increases must distribute exactly 2 points, "
                    "at most 2 to a single ability"
                ),
            )
        for ability, points in increases.items():
            if points == 0:
                continue
            score = next(
                (s for s in character.ability_scores if s.ability == ability), None
            )
            if score is None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail=f"Character has no {ability} score",
                )
            new_total = score.base_score + score.asi_bonus + score.misc_bonus + points
            if new_total > 20:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail=f"{ability} cannot exceed 20",
                )
            score.asi_bonus += points

    async def _apply_feat_selection(
        self, character: Character, feat_id: uuid.UUID, db: AsyncSession
    ) -> None:
        """Validate a feat's prerequisites and record it as a character feature."""
        feat = await catalog_service.get_feat(db, feat_id)
        if feat is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Feat not found"
            )
        for prereq in feat.prerequisites:
            if prereq.ability_score_id is None:
                continue
            ability_def = await catalog_service.get_ability_score(
                db, prereq.ability_score_id
            )
            if ability_def is None:
                continue
            score = next(
                (
                    s
                    for s in character.ability_scores
                    if s.ability.value == ability_def.index
                ),
                None,
            )
            current = (
                score.base_score + score.asi_bonus + score.misc_bonus
                if score is not None
                else 0
            )
            if current < prereq.minimum_score:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail=(
                        f"Doesn't meet this feat's prerequisite: "
                        f"{ability_def.index} {prereq.minimum_score}"
                    ),
                )

        feat_read = await catalog_service.get_feat_translated(db, feat_id)
        feat_name = feat_read.name if feat_read is not None else "Feat"
        db.add(
            CharacterFeature(
                character_id=character.id,
                source_type=FeatureSourceType.feat,
                source_name=feat_name,
                feature_name=feat_name,
                description=feat_read.description if feat_read is not None else None,
                level_acquired=character.level,
            )
        )

    async def _apply_feature_choices(
        self,
        character: Character,
        class_level_row: ClassLevel | None,
        data: CharacterLevelUpRequest,
        db: AsyncSession,
    ) -> None:
        """Require and persist a choice for every choice feature granted this level.

        A "choice feature" is any `Feature` granted at `class_level_row`
        that has named options (other `Feature` rows with
        `parent_feature_id` set to it — e.g. "Fighting Style" -> "Fighting
        Style: Dueling"). Every such feature must have a matching entry in
        `data.feature_choices`, or the whole level-up is rejected (422,
        nothing committed) with `requires_choice`/the available options so
        the client can retry with a pick.
        """
        if class_level_row is None:
            return
        granted_features = [clf.feature for clf in class_level_row.level_features]

        pending: list[dict[str, Any]] = []
        to_persist: list[CharacterFeatureChoiceInput] = []
        for feature in granted_features:
            options_result = await db.execute(
                select(Feature).where(Feature.parent_feature_id == feature.id)
            )
            option_ids = {o.id for o in options_result.scalars().all()}
            if not option_ids:
                continue

            choice = next(
                (c for c in data.feature_choices if c.feature_id == feature.id), None
            )
            if choice is None:
                pending.append(
                    {
                        "feature_id": feature.id,
                        "options": await catalog_service.list_features_translated(
                            db, parent_feature_id=feature.id
                        ),
                    }
                )
                continue
            if choice.feature_option_id not in option_ids:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail=(
                        f"{choice.feature_option_id} is not an option of feature "
                        f"{feature.id}"
                    ),
                )
            to_persist.append(choice)

        if pending:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail={
                    "requires_choice": True,
                    "choices": [
                        {
                            "feature_id": str(p["feature_id"]),
                            "options": [
                                {"id": str(o.id), "name": o.feature_name}
                                for o in p["options"]
                            ],
                        }
                        for p in pending
                    ],
                },
            )

        for choice in to_persist:
            db.add(
                CharacterFeatureChoice(
                    character_id=character.id,
                    feature_id=choice.feature_id,
                    feature_option_id=choice.feature_option_id,
                )
            )

    async def list_characters_for_campaign(
        self, campaign_id: uuid.UUID, requester_id: uuid.UUID, db: AsyncSession
    ) -> list[CharacterRead | CharacterSummaryRead]:
        """List every character in `campaign_id`. Viewable by any of its members.

        The character's own player and the campaign's DM get the full
        `CharacterRead`; every other member gets a `CharacterSummaryRead`
        (name/race/classes/level only — no ability scores, HP, spells, or
        equipment).
        """
        membership_result = await db.execute(
            select(CampaignMember).where(
                CampaignMember.campaign_id == campaign_id,
                CampaignMember.user_id == requester_id,
            )
        )
        requester_member = membership_result.scalar_one_or_none()
        if requester_member is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this campaign",
            )
        is_dm = requester_member.role == CampaignRole.dm

        result = await db.execute(
            select(Character)
            .join(CampaignMember, CampaignMember.id == Character.campaign_member_id)
            .where(CampaignMember.campaign_id == campaign_id)
            .options(*_CHARACTER_LOAD_OPTIONS)
        )
        characters = list(result.scalars().all())
        all_spell_ids = list(
            {s.spell_id for c in characters for s in c.spells}
        )
        spells = await catalog_service.get_spells_by_ids(db, all_spell_ids)
        spell_catalog = {s.id: s for s in spells}

        member_ids = {c.campaign_member_id for c in characters}
        members_result = await db.execute(
            select(CampaignMember).where(CampaignMember.id.in_(member_ids))
        )
        owner_user_id_by_member_id = {
            m.id: m.user_id for m in members_result.scalars().all()
        }

        reads: list[CharacterRead | CharacterSummaryRead] = []
        for c in characters:
            owns_it = owner_user_id_by_member_id.get(c.campaign_member_id) == (
                requester_id
            )
            if is_dm or owns_it:
                max_slots = await self._max_spell_slots(c, db)
                max_resources = await self._max_resources(c, db)
                reads.append(
                    self._to_read(c, spell_catalog, max_slots, max_resources)
                )
            else:
                reads.append(self._to_summary(c))
        return reads

    def _to_summary(self, character: Character) -> CharacterSummaryRead:
        """Build the restricted read schema shown for another player's character."""
        return CharacterSummaryRead(
            id=character.id,
            campaign_member_id=character.campaign_member_id,
            name=character.name,
            race_id=character.race_id,
            subrace_id=character.subrace_id,
            level=character.level,
            classes=[CharacterClassRead.model_validate(c) for c in character.classes],
        )

    async def update_character(
        self,
        character_id: uuid.UUID,
        requester_id: uuid.UUID,
        data: CharacterUpdate,
        db: AsyncSession,
    ) -> CharacterRead:
        """Update a character's combat-facing fields (HP/AC/inspiration).

        Only the character's own player may do this — mirrors `add_class`.
        """
        result = await db.execute(
            select(Character)
            .where(Character.id == character_id)
            .options(*_CHARACTER_LOAD_OPTIONS)
        )
        character = result.scalar_one_or_none()
        if character is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Character not found"
            )
        await self._require_own_membership(
            character.campaign_member_id, requester_id, db
        )

        if data.hit_point_current is not None:
            if data.hit_point_current > character.hit_point_max:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail="hit_point_current cannot exceed hit_point_max",
                )
            old_hp = character.hit_point_current
            character.hit_point_current = data.hit_point_current
            self._register_hp_change(character, old_hp, data.hit_point_current)
        if data.temporary_hit_points is not None:
            character.temporary_hit_points = data.temporary_hit_points
        if data.armor_class is not None:
            character.armor_class = data.armor_class
        if data.inspiration is not None:
            character.inspiration = data.inspiration

        await db.commit()
        return await self._reload_as_read(character.id, db)

    async def add_spell(
        self,
        character_id: uuid.UUID,
        requester_id: uuid.UUID,
        data: CharacterSpellCreate,
        db: AsyncSession,
    ) -> CharacterRead:
        """Add a known/prepared spell to a character. Owner only."""
        character = await self._load_character_owned_by(
            character_id, requester_id, db
        )

        spell = await catalog_service.get_spell(db, data.spell_id)
        if spell is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Spell not found"
            )
        member_result = await db.execute(
            select(CampaignMember).where(
                CampaignMember.id == character.campaign_member_id
            )
        )
        member = member_result.scalar_one()
        self._validate_reference(spell, member.campaign_id)

        await self._validate_spell_limit(
            character, spell, data.source_class, data.prepared, db
        )

        db.add(
            CharacterSpell(
                character_id=character.id,
                spell_id=data.spell_id,
                prepared=data.prepared,
                source_class=data.source_class,
            )
        )
        await db.commit()
        return await self._reload_as_read(character.id, db)

    async def update_spell(
        self,
        character_id: uuid.UUID,
        spell_entry_id: uuid.UUID,
        requester_id: uuid.UUID,
        data: CharacterSpellUpdate,
        db: AsyncSession,
    ) -> CharacterRead:
        """Toggle a known spell's `prepared` flag. Owner only.

        Preparing (not unpreparing) re-checks the prepared-caster limit —
        see `_validate_spell_limit`.
        """
        character = await self._load_character_owned_by(
            character_id, requester_id, db
        )
        entry = self._require_spell_entry(character, spell_entry_id)

        if data.prepared:
            spell = await catalog_service.get_spell(db, entry.spell_id)
            if spell is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Spell not found"
                )
            await self._validate_spell_limit(
                character,
                spell,
                entry.source_class,
                True,
                db,
                exclude_spell_entry_id=entry.id,
            )

        entry.prepared = data.prepared
        await db.commit()
        return await self._reload_as_read(character.id, db)

    async def remove_spell(
        self,
        character_id: uuid.UUID,
        spell_entry_id: uuid.UUID,
        requester_id: uuid.UUID,
        db: AsyncSession,
    ) -> CharacterRead:
        """Forget a known spell. Owner only."""
        character = await self._load_character_owned_by(
            character_id, requester_id, db
        )
        entry = self._require_spell_entry(character, spell_entry_id)
        await db.delete(entry)
        await db.commit()
        return await self._reload_as_read(character.id, db)

    async def cast_spell(
        self,
        character_id: uuid.UUID,
        spell_entry_id: uuid.UUID,
        requester_id: uuid.UUID,
        data: CharacterSpellCastRequest,
        db: AsyncSession,
    ) -> CharacterSpellCastResponse:
        """Cast a known spell, consuming a spell slot. Owner only.

        Cantrips and rituals never consume a slot. Casting above the
        spell's own level ("upcasting") consumes a slot of the level
        requested via `cast_at_level`, and requires that slot to exist.
        `target_participant_id`/`save_dc` are cast context, not character
        state — see `CharacterSpellCastResponse`.
        """
        character = await self._load_character_owned_by(
            character_id, requester_id, db
        )
        entry = self._require_spell_entry(character, spell_entry_id)
        spell = await catalog_service.get_spell(db, entry.spell_id)
        if spell is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Spell not found"
            )

        if data.as_ritual and not spell.ritual:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="This spell cannot be cast as a ritual",
            )

        class_match = (
            await self._find_class_by_index(character, entry.source_class, db)
            if entry.source_class is not None
            else None
        )
        requires_prepared = (
            spell.level > 0
            and not data.as_ritual
            and class_match is not None
            and class_match[1].index in PREPARED_CASTER_CLASSES
        )
        if requires_prepared and not entry.prepared:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Spell must be prepared to cast",
            )

        # Casting any concentration spell replaces whatever the character was
        # already concentrating on — only one at a time (PHB rule).
        if spell.concentration:
            character.concentrating_spell_id = spell.id

        save_dc = (
            self._spell_save_dc(character, class_match[1])
            if spell.action_type == SpellActionType.saving_throw
            and class_match is not None
            else None
        )

        if spell.level == 0 or data.as_ritual:
            await db.commit()
            return CharacterSpellCastResponse(
                character=await self._reload_as_read(character.id, db),
                save_dc=save_dc,
                target_participant_id=data.target_participant_id,
            )

        cast_at_level = data.cast_at_level or spell.level
        if cast_at_level < spell.level:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=(
                    f"Cannot cast a level {spell.level} spell using a level "
                    f"{cast_at_level} slot"
                ),
            )

        max_slots = await self._max_spell_slots(character, db)
        limit = max_slots.get(cast_at_level, 0)
        slot = next(
            (s for s in character.spell_slots if s.spell_level == cast_at_level),
            None,
        )
        used = slot.used if slot is not None else 0
        if used >= limit:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=(
                    f"No level {cast_at_level} spell slots remaining "
                    f"({used}/{limit} used)"
                ),
            )

        if slot is None:
            slot = CharacterSpellSlot(
                character_id=character.id, spell_level=cast_at_level, used=0
            )
            db.add(slot)
        slot.used += 1
        await db.commit()
        return CharacterSpellCastResponse(
            character=await self._reload_as_read(character.id, db),
            save_dc=save_dc,
            target_participant_id=data.target_participant_id,
        )

    def _spell_save_dc(
        self, character: Character, class_def: ClassDefinition
    ) -> int | None:
        """`8 + proficiency + spellcasting ability modifier`, PHB spell save DC.

        `None` when `class_def` has no spellcasting ability (shouldn't
        happen for a class that granted a `saving_throw` spell, but avoids
        a crash if the catalog data is ever inconsistent).
        """
        if class_def.spellcasting_ability is None:
            return None
        ability_mod = self._ability_modifier(character, class_def.spellcasting_ability)
        return 8 + character.proficiency_bonus + ability_mod

    async def rest(
        self,
        character_id: uuid.UUID,
        requester_id: uuid.UUID,
        data: CharacterRestRequest,
        db: AsyncSession,
    ) -> CharacterRead:
        """Take a short or long rest. Owner only.

        A long rest resets every spell slot's `used` count to 0, and
        restores spent hit dice up to half the character's total hit dice
        (minimum 1), PHB rule — dice are restored class by class, in the
        order the character's classes were added, until that cap is spent.
        A short rest doesn't affect slots by default — Warlock's
        short-rest slot recovery is a separate class rule, out of scope
        here — but may spend hit dice (`data.hit_dice_spent`) to heal. Both
        rest types also restore class resources (rage, ki, ...) whose
        `_RESOURCE_RECHARGE` entry matches — a long rest restores short-rest
        resources too, PHB rule.
        """
        character = await self._load_character_owned_by(
            character_id, requester_id, db
        )
        if data.rest_type == "long":
            for slot in character.spell_slots:
                slot.used = 0
            total_dice = sum(c.level for c in character.classes)
            remaining = max(1, total_dice // 2)
            for class_entry in character.classes:
                if remaining <= 0:
                    break
                restored = min(class_entry.hit_dice_used, remaining)
                class_entry.hit_dice_used -= restored
                remaining -= restored
        else:
            await self._spend_hit_dice(character, data.hit_dice_spent, db)
        for resource in character.resources:
            recharge = _RESOURCE_RECHARGE.get(resource.resource_key)
            if recharge == "short" or (
                recharge == "long" and data.rest_type == "long"
            ):
                resource.used = 0
        await db.commit()
        return await self._reload_as_read(character.id, db)

    async def _spend_hit_dice(
        self,
        character: Character,
        spends: list[CharacterHitDiceSpend],
        db: AsyncSession,
    ) -> None:
        """Roll and apply healing for each class's hit dice spent on a short rest.

        Each die rolled is the spending class's `hit_die` plus the
        character's CON modifier (never healing below 0, and never past
        `hit_point_max`), unless `manual_roll` is supplied instead.
        """
        con_mod = self._ability_modifier(character, "con")
        for spend in spends:
            class_entry = next(
                (c for c in character.classes if c.id == spend.character_class_id),
                None,
            )
            if class_entry is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Character class not found on this character",
                )
            available = class_entry.level - class_entry.hit_dice_used
            if spend.count > available:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail=(
                        f"Not enough hit dice available "
                        f"({available} left, {spend.count} requested)"
                    ),
                )
            if spend.manual_roll is not None:
                healed = spend.manual_roll
            else:
                class_def = await catalog_service.get_class(
                    db, class_entry.class_definition_id
                )
                if class_def is None:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Class not found",
                    )
                roll_result = dice.roll(f"{spend.count}d{class_def.hit_die}")
                healed = max(0, roll_result.total + con_mod * spend.count)
            old_hp = character.hit_point_current
            character.hit_point_current = min(
                character.hit_point_max, character.hit_point_current + healed
            )
            self._register_hp_change(character, old_hp, character.hit_point_current)
            class_entry.hit_dice_used += spend.count

    async def use_resource(
        self,
        character_id: uuid.UUID,
        requester_id: uuid.UUID,
        resource_key: str,
        db: AsyncSession,
        *,
        option_id: uuid.UUID | None = None,
    ) -> CharacterRead:
        """Spend one use of a class resource (rage, ki, ...). Owner only.

        Rejects a `resource_key` the character doesn't have (either not in
        `_RESOURCE_RECHARGE`, or granted by none of their classes at their
        current level) or one already at its limit. Restored by `rest`.

        `option_id` records which named option the use spent (e.g. a
        Paladin's Channel Divinity: Sacred Weapon vs. Turn the Unholy) —
        required when the character has more than one option for this
        resource, optional (and ignored) when they have none or exactly
        one, see `_RESOURCE_OPTION_PARENT_FEATURES`.
        """
        character = await self._load_character_owned_by(
            character_id, requester_id, db
        )
        if resource_key not in _RESOURCE_RECHARGE:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"{resource_key} isn't a trackable class resource",
            )
        max_resources = await self._max_resources(character, db)
        limit = max_resources.get(resource_key, 0)
        if limit <= 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"Character doesn't have the {resource_key} resource",
            )

        entry = next(
            (r for r in character.resources if r.resource_key == resource_key), None
        )
        used = entry.used if entry is not None else 0
        if used >= limit:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"No {resource_key} uses remaining ({used}/{limit} used)",
            )

        options = await self._resource_options(character, resource_key, db)
        if len(options) > 1:
            option_ids = {o.id for o in options}
            if option_id is None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail=(
                        f"{resource_key} has more than one option for this "
                        "character — option_id is required"
                    ),
                )
            if option_id not in option_ids:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail=f"{option_id} is not a {resource_key} option",
                )

        if entry is None:
            entry = CharacterResource(
                character_id=character.id, resource_key=resource_key, used=0
            )
            db.add(entry)
        entry.used += 1
        if option_id is not None:
            entry.last_feature_option_id = option_id
        await db.commit()
        return await self._reload_as_read(character.id, db)

    async def _resource_options(
        self, character: Character, resource_key: str, db: AsyncSession
    ) -> list[Feature]:
        """Return the named options available to `character` for `resource_key`.

        Empty when `resource_key` has no option concept, or when none of
        its parent features (`_RESOURCE_OPTION_PARENT_FEATURES`) match a
        class/subclass the character actually has.
        """
        parent_indexes = _RESOURCE_OPTION_PARENT_FEATURES.get(resource_key)
        if not parent_indexes:
            return []

        class_ids = {c.class_definition_id for c in character.classes}
        subclass_ids = {
            c.subclass_id for c in character.classes if c.subclass_id is not None
        }

        parents_result = await db.execute(
            select(Feature).where(Feature.index.in_(parent_indexes))
        )
        relevant_parent_ids = [
            p.id
            for p in parents_result.scalars().all()
            if (p.class_definition_id is None or p.class_definition_id in class_ids)
            and (
                p.subclass_definition_id is None
                or p.subclass_definition_id in subclass_ids
            )
        ]
        if not relevant_parent_ids:
            return []

        options_result = await db.execute(
            select(Feature).where(Feature.parent_feature_id.in_(relevant_parent_ids))
        )
        return [
            o
            for o in options_result.scalars().all()
            if (o.class_definition_id is None or o.class_definition_id in class_ids)
            and (
                o.subclass_definition_id is None
                or o.subclass_definition_id in subclass_ids
            )
        ]

    async def death_save(
        self,
        character_id: uuid.UUID,
        requester_id: uuid.UUID,
        data: CharacterDeathSaveRequest,
        db: AsyncSession,
    ) -> CharacterRead:
        """Roll a death saving throw. Owner only, only at 0 hit points.

        1 counts as two failures; 20 restores 1 HP and consciousness
        (resetting the track); 10+ is a success, anything else a failure.
        Three failures marks the character dead; three successes
        stabilizes them (track resets, still unconscious at 0 HP).
        """
        character = await self._load_character_owned_by(
            character_id, requester_id, db
        )
        if character.is_dead:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Character is already dead",
            )
        if character.hit_point_current != 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Death saves only apply at 0 hit points",
            )

        if data.manual_roll is not None:
            roll_result = data.manual_roll
        else:
            roll_result = dice.roll("1d20").total

        if roll_result == 1:
            character.death_save_failures = min(3, character.death_save_failures + 2)
        elif roll_result == 20:
            character.hit_point_current = 1
            character.death_save_successes = 0
            character.death_save_failures = 0
        elif roll_result >= 10:
            character.death_save_successes = min(3, character.death_save_successes + 1)
        else:
            character.death_save_failures = min(3, character.death_save_failures + 1)

        if character.death_save_failures >= 3:
            character.is_dead = True
        elif character.death_save_successes >= 3:
            character.death_save_successes = 0
            character.death_save_failures = 0

        await db.commit()
        return await self._reload_as_read(character.id, db)

    async def set_concentration(
        self,
        character_id: uuid.UUID,
        requester_id: uuid.UUID,
        data: CharacterConcentrationRequest,
        db: AsyncSession,
    ) -> CharacterRead:
        """Start or end concentration on a known spell. Owner only.

        Starting replaces whatever the character was already concentrating
        on — only one at a time (PHB rule); see also `cast_spell`, which
        does the same automatically when casting a concentration spell.
        """
        character = await self._load_character_owned_by(
            character_id, requester_id, db
        )
        if data.spell_id is None:
            character.concentrating_spell_id = None
            await db.commit()
            return await self._reload_as_read(character.id, db)

        entry = next(
            (s for s in character.spells if s.spell_id == data.spell_id), None
        )
        if entry is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Spell not known by this character",
            )
        spell = await catalog_service.get_spell(db, data.spell_id)
        if spell is None or not spell.concentration:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="This spell doesn't require concentration",
            )
        character.concentrating_spell_id = data.spell_id
        await db.commit()
        return await self._reload_as_read(character.id, db)

    async def add_equipment(
        self,
        character_id: uuid.UUID,
        requester_id: uuid.UUID,
        data: CharacterEquipmentCreate,
        db: AsyncSession,
    ) -> CharacterRead:
        """Add an item to a character's personal inventory. Owner only."""
        character = await self._load_character_owned_by(
            character_id, requester_id, db
        )

        item = await catalog_service.get_item(db, data.item_id)
        if item is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Item not found"
            )
        member_result = await db.execute(
            select(CampaignMember).where(
                CampaignMember.id == character.campaign_member_id
            )
        )
        member = member_result.scalar_one()
        self._validate_reference(item, member.campaign_id)

        db.add(
            CharacterEquipment(
                character_id=character.id,
                item_id=data.item_id,
                equipped=data.equipped,
                quantity=data.quantity,
                attunement=data.attunement,
            )
        )
        await db.commit()
        return await self._reload_as_read(character.id, db)

    async def update_equipment(
        self,
        character_id: uuid.UUID,
        equipment_id: uuid.UUID,
        requester_id: uuid.UUID,
        data: CharacterEquipmentUpdate,
        db: AsyncSession,
    ) -> CharacterRead:
        """Edit an inventory item (equipped/attunement/quantity). Owner only."""
        character = await self._load_character_owned_by(
            character_id, requester_id, db
        )
        entry = self._require_equipment_entry(character, equipment_id)

        if data.equipped is not None:
            entry.equipped = data.equipped
        if data.attunement is not None:
            entry.attunement = data.attunement
        if data.quantity is not None:
            entry.quantity = data.quantity

        await db.commit()
        return await self._reload_as_read(character.id, db)

    async def remove_equipment(
        self,
        character_id: uuid.UUID,
        equipment_id: uuid.UUID,
        requester_id: uuid.UUID,
        db: AsyncSession,
    ) -> CharacterRead:
        """Remove an item from a character's inventory. Owner only."""
        character = await self._load_character_owned_by(
            character_id, requester_id, db
        )
        entry = self._require_equipment_entry(character, equipment_id)
        await db.delete(entry)
        await db.commit()
        return await self._reload_as_read(character.id, db)

    async def update_currency(
        self,
        character_id: uuid.UUID,
        requester_id: uuid.UUID,
        data: CharacterCurrencyRequest,
        db: AsyncSession,
    ) -> CharacterRead:
        """Record a currency gain (positive `delta`) or spend (negative). Owner only.

        The resulting balance can never go below zero (422).
        """
        character = await self._load_character_owned_by(
            character_id, requester_id, db
        )
        new_balance = character.currency_cp + data.delta
        if new_balance < 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=(
                    f"Insufficient funds: balance is {character.currency_cp} cp, "
                    f"cannot spend {-data.delta} cp"
                ),
            )
        character.currency_cp = new_balance
        await db.commit()
        return await self._reload_as_read(character.id, db)

    def _require_equipment_entry(
        self, character: Character, equipment_id: uuid.UUID
    ) -> CharacterEquipment:
        """Return the character's `CharacterEquipment` row, 404 if not on this sheet."""
        entry = next(
            (e for e in character.equipment if e.id == equipment_id), None
        )
        if entry is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Equipment entry not found on this character",
            )
        return entry

    async def add_feature(
        self,
        character_id: uuid.UUID,
        requester_id: uuid.UUID,
        data: CharacterFeatureCreate,
        db: AsyncSession,
    ) -> CharacterRead:
        """Record a class/feat feature on a character. Owner only.

        Free-text (`source_name`/`feature_name`/`description`), not a
        catalog reference — see `CharacterFeatureCreate`.
        """
        character = await self._load_character_owned_by(
            character_id, requester_id, db
        )
        db.add(
            CharacterFeature(
                character_id=character.id,
                source_type=data.source_type,
                source_name=data.source_name,
                feature_name=data.feature_name,
                description=data.description,
                level_acquired=data.level_acquired,
            )
        )
        await db.commit()
        return await self._reload_as_read(character.id, db)

    async def _load_character_owned_by(
        self, character_id: uuid.UUID, requester_id: uuid.UUID, db: AsyncSession
    ) -> Character:
        """Load a character, 404 if missing, 403 unless `requester_id` owns it."""
        result = await db.execute(
            select(Character)
            .where(Character.id == character_id)
            .options(*_CHARACTER_LOAD_OPTIONS)
        )
        character = result.scalar_one_or_none()
        if character is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Character not found"
            )
        await self._require_own_membership(
            character.campaign_member_id, requester_id, db
        )
        return character

    def _require_spell_entry(
        self, character: Character, spell_entry_id: uuid.UUID
    ) -> CharacterSpell:
        """Return the character's `CharacterSpell` row, 404 if not on this sheet."""
        entry = next(
            (s for s in character.spells if s.id == spell_entry_id), None
        )
        if entry is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Spell entry not found on this character",
            )
        return entry

    async def _find_class_by_index(
        self, character: Character, class_index: str, db: AsyncSession
    ) -> tuple[CharacterClass, ClassDefinition] | None:
        """Find the character's `CharacterClass` whose class has `index`."""
        for class_entry in character.classes:
            class_def = await catalog_service.get_class(
                db, class_entry.class_definition_id
            )
            if class_def is not None and class_def.index == class_index:
                return class_entry, class_def
        return None

    def _class_level_row(
        self, class_def: ClassDefinition, level: int
    ) -> ClassLevel | None:
        """Return the base (non-subclass) `ClassLevel` row for `level`."""
        return next(
            (
                cl
                for cl in class_def.class_levels
                if cl.subclass_definition_id is None and cl.level == level
            ),
            None,
        )

    async def _max_spell_slots(
        self, character: Character, db: AsyncSession
    ) -> dict[int, int]:
        """Sum each casting class's own spell-slot maxima, keyed by level 1-9.

        See `CharacterSpellSlot`'s docstring for the multiclass
        simplification this sum makes.
        """
        totals: dict[int, int] = {}
        for class_entry in character.classes:
            class_def = await catalog_service.get_class(
                db, class_entry.class_definition_id
            )
            if class_def is None:
                continue
            class_level = self._class_level_row(class_def, class_entry.level)
            if class_level is None:
                continue
            for slot in class_level.spell_slots:
                if slot.spell_level == 0:
                    continue
                totals[slot.spell_level] = (
                    totals.get(slot.spell_level, 0) + slot.slot_count
                )
        return totals

    async def _max_resources(
        self, character: Character, db: AsyncSession
    ) -> dict[str, int]:
        """Sum each class's trackable resource maxima, keyed by `resource_key`.

        Only keys in `_RESOURCE_RECHARGE` are included — see its docstring.
        A `ClassLevelResource.value` that isn't a plain integer (a few are,
        e.g. `sneak_attack_dice: "2d6"`) is skipped; none of the currently
        trackable keys are dice expressions, but this keeps a future
        catalog addition from crashing instead of just being ignored.
        """
        totals: dict[str, int] = {}
        for class_entry in character.classes:
            class_def = await catalog_service.get_class(
                db, class_entry.class_definition_id
            )
            if class_def is None:
                continue
            class_level = self._class_level_row(class_def, class_entry.level)
            if class_level is None:
                continue
            for resource in class_level.resources:
                if resource.resource_key not in _RESOURCE_RECHARGE:
                    continue
                try:
                    value = int(resource.value)
                except ValueError:
                    continue
                totals[resource.resource_key] = (
                    totals.get(resource.resource_key, 0) + value
                )
        return totals

    def _register_hp_change(
        self, character: Character, old_hp: int, new_hp: int
    ) -> None:
        """Apply death-save bookkeeping for a change to `hit_point_current`.

        Rising above 0 (healed) resets the death-save track. Taking more
        damage while already at 0 — the caller floors HP at 0 before
        calling, same convention `app.combat.service` uses for
        `EncounterParticipant` — counts as one more failure, marking the
        character dead at three. A natural-20 crit doubling this failure
        isn't modeled here: this generic HP setter carries no crit context,
        unlike `death_save`'s own 1d20 roll where a natural 1 does double.
        """
        if new_hp > 0:
            character.death_save_successes = 0
            character.death_save_failures = 0
            return
        if old_hp == 0 and new_hp == 0:
            character.death_save_successes = 0
            character.death_save_failures = min(3, character.death_save_failures + 1)
            if character.death_save_failures >= 3:
                character.is_dead = True

    def _ability_modifier(self, character: Character, ability_code: str) -> int:
        """Return the character's modifier for a short ability code (e.g. `wis`)."""
        for score in character.ability_scores:
            if score.ability.value == ability_code:
                return calculate_modifier(
                    score.base_score + score.asi_bonus + score.misc_bonus
                )
        return 0

    async def _count_known_spells(
        self,
        character_id: uuid.UUID,
        class_index: str,
        *,
        cantrip: bool,
        db: AsyncSession,
        exclude_spell_entry_id: uuid.UUID | None = None,
    ) -> int:
        """Count a character's known spells for one class (cantrips or not)."""
        stmt = (
            select(func.count(CharacterSpell.id))
            .join(Spell, Spell.id == CharacterSpell.spell_id)
            .where(
                CharacterSpell.character_id == character_id,
                CharacterSpell.source_class == class_index,
                (Spell.level == 0) if cantrip else (Spell.level > 0),
            )
        )
        if exclude_spell_entry_id is not None:
            stmt = stmt.where(CharacterSpell.id != exclude_spell_entry_id)
        result = await db.execute(stmt)
        return result.scalar_one()

    async def _count_prepared_spells(
        self,
        character_id: uuid.UUID,
        class_index: str,
        db: AsyncSession,
        exclude_spell_entry_id: uuid.UUID | None = None,
    ) -> int:
        """Count a character's prepared (non-cantrip) spells for one class."""
        stmt = (
            select(func.count(CharacterSpell.id))
            .join(Spell, Spell.id == CharacterSpell.spell_id)
            .where(
                CharacterSpell.character_id == character_id,
                CharacterSpell.source_class == class_index,
                CharacterSpell.prepared.is_(True),
                Spell.level > 0,
            )
        )
        if exclude_spell_entry_id is not None:
            stmt = stmt.where(CharacterSpell.id != exclude_spell_entry_id)
        result = await db.execute(stmt)
        return result.scalar_one()

    async def _validate_spell_limit(
        self,
        character: Character,
        spell: Spell,
        source_class: str | None,
        prepared: bool,
        db: AsyncSession,
        *,
        exclude_spell_entry_id: uuid.UUID | None = None,
    ) -> None:
        """Enforce the known/prepared spell limit for `source_class` (422).

        No-op when `source_class` doesn't match one of the character's
        classes — a limit can't be computed without knowing whose
        progression to use (see `engine.spellcasting`).
        """
        if source_class is None:
            return
        match = await self._find_class_by_index(character, source_class, db)
        if match is None:
            return
        class_entry, class_def = match

        if class_def.index in KNOWN_CASTER_CLASSES:
            class_level = self._class_level_row(class_def, class_entry.level)
            if class_level is None:
                return
            if spell.level == 0:
                limit = next(
                    (
                        s.slot_count
                        for s in class_level.spell_slots
                        if s.spell_level == 0
                    ),
                    0,
                )
                kind = "cantrips"
            else:
                resource = next(
                    (
                        r
                        for r in class_level.resources
                        if r.resource_key == "spells_known"
                    ),
                    None,
                )
                limit = int(resource.value) if resource is not None else 0
                kind = "spells known"
            current = await self._count_known_spells(
                character.id,
                class_def.index,
                cantrip=spell.level == 0,
                db=db,
                exclude_spell_entry_id=exclude_spell_entry_id,
            )
            if current >= limit:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail=(
                        f"{class_def.index} already knows the maximum of {limit} "
                        f"{kind} at level {class_entry.level} ({current} known)"
                    ),
                )
            return

        if (
            prepared
            and spell.level > 0
            and class_def.index in PREPARED_CASTER_CLASSES
            and class_def.spellcasting_ability is not None
        ):
            ability_mod = self._ability_modifier(
                character, class_def.spellcasting_ability
            )
            limit = prepared_spell_limit(ability_mod, class_entry.level)
            current = await self._count_prepared_spells(
                character.id,
                class_def.index,
                db,
                exclude_spell_entry_id=exclude_spell_entry_id,
            )
            if current >= limit:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail=(
                        f"{class_def.index} can only prepare {limit} spells at "
                        f"level {class_entry.level} ({current} prepared)"
                    ),
                )

    async def _current_class_indices(
        self, character: Character, db: AsyncSession
    ) -> list[str]:
        """Return the SRD `index` of each class the character already has."""
        indices = []
        for class_entry in character.classes:
            class_def = await catalog_service.get_class(
                db, class_entry.class_definition_id
            )
            if class_def is not None and class_def.index is not None:
                indices.append(class_def.index)
        return indices

    async def _require_viewer(
        self, character: Character, requester_id: uuid.UUID, db: AsyncSession
    ) -> None:
        """Raise 403 unless `requester_id` owns the sheet or DMs its campaign."""
        result = await db.execute(
            select(CampaignMember).where(
                CampaignMember.id == character.campaign_member_id
            )
        )
        owning_member = result.scalar_one_or_none()
        if owning_member is not None and owning_member.user_id == requester_id:
            return
        if owning_member is not None:
            dm_result = await db.execute(
                select(CampaignMember).where(
                    CampaignMember.campaign_id == owning_member.campaign_id,
                    CampaignMember.user_id == requester_id,
                    CampaignMember.role == CampaignRole.dm,
                )
            )
            if dm_result.scalar_one_or_none() is not None:
                return
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot view another player's character",
        )

    async def _reload_as_read(
        self, character_id: uuid.UUID, db: AsyncSession
    ) -> CharacterRead:
        """Reload a character with relationships, as a read schema.

        `populate_existing` forces fresh relationship collections even when
        the `Character` (and a stale `.classes`/`.ability_scores`) is already
        in the session's identity map from an earlier query in this request
        (e.g. `add_class` loading it before appending a new class).
        """
        result = await db.execute(
            select(Character)
            .where(Character.id == character_id)
            .options(*_CHARACTER_LOAD_OPTIONS)
            .execution_options(populate_existing=True)
        )
        character = result.scalar_one()
        spell_catalog = await self._resolve_spell_catalog(character, db)
        max_slots = await self._max_spell_slots(character, db)
        max_resources = await self._max_resources(character, db)
        return self._to_read(character, spell_catalog, max_slots, max_resources)

    async def _resolve_spell_catalog(
        self, character: Character, db: AsyncSession
    ) -> dict[uuid.UUID, Spell]:
        """Bulk-fetch the catalog `Spell` rows for a character's known spells."""
        spells = await catalog_service.get_spells_by_ids(
            db, [s.spell_id for s in character.spells]
        )
        return {s.id: s for s in spells}

    def _to_read(
        self,
        character: Character,
        spell_catalog: dict[uuid.UUID, Spell],
        max_slots: dict[int, int],
        max_resources: dict[str, int],
    ) -> CharacterRead:
        """Build the read schema, computing ability modifiers and skill bonuses."""
        modifier_by_ability = {
            score.ability: calculate_modifier(
                score.base_score + score.asi_bonus + score.misc_bonus
            )
            for score in character.ability_scores
        }
        ability_scores = [
            CharacterAbilityScoreRead(
                id=score.id,
                ability=score.ability,
                base_score=score.base_score,
                asi_bonus=score.asi_bonus,
                misc_bonus=score.misc_bonus,
                modifier=modifier_by_ability[score.ability],
                save_proficient=score.save_proficient,
                save_bonus=calculate_saving_throw_bonus(
                    modifier_by_ability[score.ability],
                    score.save_proficient,
                    character.proficiency_bonus,
                ),
            )
            for score in character.ability_scores
        ]
        skills = [
            CharacterSkillRead(
                id=skill.id,
                skill=skill.skill,
                ability=SKILL_ABILITY[skill.skill],
                proficient=skill.proficient,
                expertise=skill.expertise,
                bonus=calculate_skill_bonus(
                    modifier_by_ability[SKILL_ABILITY[skill.skill]],
                    skill.proficient,
                    skill.expertise,
                    character.proficiency_bonus,
                ),
            )
            for skill in character.skills
        ]
        bonus_by_skill = {s.skill: s.bonus for s in skills}
        passive_perception = 10 + bonus_by_skill.get(Skill.perception, 0)
        passive_investigation = 10 + bonus_by_skill.get(Skill.investigation, 0)
        passive_insight = 10 + bonus_by_skill.get(Skill.insight, 0)
        classes = [CharacterClassRead.model_validate(c) for c in character.classes]
        spells = [
            CharacterSpellRead(
                id=s.id,
                spell_id=s.spell_id,
                prepared=s.prepared,
                source_class=s.source_class,
                level=spell_catalog[s.spell_id].level
                if s.spell_id in spell_catalog
                else 0,
                ritual=spell_catalog[s.spell_id].ritual
                if s.spell_id in spell_catalog
                else False,
            )
            for s in character.spells
        ]
        spell_slots = [
            CharacterSpellSlotRead(
                spell_level=level,
                used=next(
                    (s.used for s in character.spell_slots if s.spell_level == level),
                    0,
                ),
                max=max_count,
            )
            for level, max_count in sorted(max_slots.items())
        ]
        equipment = [
            CharacterEquipmentRead.model_validate(e) for e in character.equipment
        ]
        features = [
            CharacterFeatureRead.model_validate(f) for f in character.features
        ]
        feature_choices = [
            CharacterFeatureChoiceRead.model_validate(c)
            for c in character.feature_choices
        ]
        used_by_resource_key = {r.resource_key: r.used for r in character.resources}
        last_option_by_resource_key = {
            r.resource_key: r.last_feature_option_id for r in character.resources
        }
        resources = [
            CharacterResourceRead(
                resource_key=resource_key,
                used=used_by_resource_key.get(resource_key, 0),
                max=max_count,
                last_feature_option_id=last_option_by_resource_key.get(resource_key),
            )
            for resource_key, max_count in sorted(max_resources.items())
        ]
        return CharacterRead(
            id=character.id,
            campaign_member_id=character.campaign_member_id,
            name=character.name,
            race_id=character.race_id,
            subrace_id=character.subrace_id,
            level=character.level,
            experience_points=character.experience_points,
            alignment=character.alignment,
            background=character.background,
            hit_point_max=character.hit_point_max,
            hit_point_current=character.hit_point_current,
            temporary_hit_points=character.temporary_hit_points,
            armor_class=character.armor_class,
            speed=character.speed,
            inspiration=character.inspiration,
            proficiency_bonus=character.proficiency_bonus,
            currency_cp=character.currency_cp,
            generation_method=character.generation_method,
            death_save_successes=character.death_save_successes,
            death_save_failures=character.death_save_failures,
            is_dead=character.is_dead,
            concentrating_spell_id=character.concentrating_spell_id,
            passive_perception=passive_perception,
            passive_investigation=passive_investigation,
            passive_insight=passive_insight,
            resources=resources,
            ability_scores=ability_scores,
            skills=skills,
            classes=classes,
            spells=spells,
            spell_slots=spell_slots,
            equipment=equipment,
            features=features,
            feature_choices=feature_choices,
        )

    async def _require_own_membership(
        self, campaign_member_id: uuid.UUID, requester_id: uuid.UUID, db: AsyncSession
    ) -> CampaignMember:
        """Fetch the campaign membership, ensuring it belongs to `requester_id`."""
        result = await db.execute(
            select(CampaignMember).where(CampaignMember.id == campaign_member_id)
        )
        member = result.scalar_one_or_none()
        if member is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign membership not found",
            )
        if member.user_id != requester_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot act on someone else's campaign membership",
            )
        return member

    def _validate_ability_scores(
        self, data: CharacterCreate
    ) -> dict[AbilityScore, CharacterAbilityScoreCreate]:
        """Ensure `data.ability_scores` has exactly one entry per ability."""
        by_ability = {score.ability: score for score in data.ability_scores}
        if len(by_ability) != len(data.ability_scores) or set(by_ability) != set(
            AbilityScore
        ):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Exactly one ability score entry is required per ability",
            )
        return by_ability

    def _validate_reference(
        self, entity: _CatalogScopedEntity, character_campaign_id: uuid.UUID
    ) -> None:
        """Raise 403 if `entity` is custom content from another campaign."""
        try:
            validate_catalog_reference(
                is_custom=entity.is_custom,
                entity_campaign_id=entity.campaign_id,
                character_campaign_id=character_campaign_id,
            )
        except CrossCampaignCatalogReferenceError as exc:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)
            ) from exc
