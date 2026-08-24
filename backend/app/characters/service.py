"""CharacterService orchestrates character sheet creation and reads."""

import uuid
from typing import Protocol

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.campaigns.domain import CampaignRole
from app.campaigns.models import CampaignMember
from app.catalog import service as catalog_service
from app.catalog.domain import AbilityScore
from app.catalog.models import ClassDefinition, ClassLevel, Spell
from app.characters.domain import (
    MULTICLASS_ABILITY_REQUIREMENTS,
    SKILL_ABILITY,
    CrossCampaignCatalogReferenceError,
    Skill,
    parse_saving_throw_proficiencies,
    validate_catalog_reference,
)
from app.characters.models import (
    Character,
    CharacterAbilityScore,
    CharacterClass,
    CharacterEquipment,
    CharacterFeature,
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
    CharacterEquipmentCreate,
    CharacterEquipmentRead,
    CharacterFeatureCreate,
    CharacterFeatureRead,
    CharacterRead,
    CharacterRestRequest,
    CharacterSkillRead,
    CharacterSpellCastRequest,
    CharacterSpellCreate,
    CharacterSpellRead,
    CharacterSpellSlotRead,
    CharacterSpellUpdate,
    CharacterUpdate,
)
from engine.abilities import (
    calculate_modifier,
    calculate_proficiency_bonus,
    calculate_saving_throw_bonus,
    calculate_skill_bonus,
)
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
)


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
        return self._to_read(character, spell_catalog, max_slots)

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

    async def list_characters_for_campaign(
        self, campaign_id: uuid.UUID, requester_id: uuid.UUID, db: AsyncSession
    ) -> list[CharacterRead]:
        """List every character in `campaign_id`. Viewable by any of its members."""
        membership_result = await db.execute(
            select(CampaignMember).where(
                CampaignMember.campaign_id == campaign_id,
                CampaignMember.user_id == requester_id,
            )
        )
        if membership_result.scalar_one_or_none() is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this campaign",
            )

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
        reads = []
        for c in characters:
            max_slots = await self._max_spell_slots(c, db)
            reads.append(self._to_read(c, spell_catalog, max_slots))
        return reads

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
            character.hit_point_current = data.hit_point_current
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
    ) -> CharacterRead:
        """Cast a known spell, consuming a spell slot. Owner only.

        Cantrips and rituals never consume a slot. Casting above the
        spell's own level ("upcasting") consumes a slot of the level
        requested via `cast_at_level`, and requires that slot to exist.
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

        if spell.level == 0 or data.as_ritual:
            return await self._reload_as_read(character.id, db)

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
        return await self._reload_as_read(character.id, db)

    async def rest(
        self,
        character_id: uuid.UUID,
        requester_id: uuid.UUID,
        data: CharacterRestRequest,
        db: AsyncSession,
    ) -> CharacterRead:
        """Take a short or long rest. Owner only.

        A long rest resets every spell slot's `used` count to 0. A short
        rest doesn't affect slots by default — Warlock's short-rest slot
        recovery is a separate class rule, out of scope here.
        """
        character = await self._load_character_owned_by(
            character_id, requester_id, db
        )
        if data.rest_type == "long":
            for slot in character.spell_slots:
                slot.used = 0
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
        return self._to_read(character, spell_catalog, max_slots)

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
            ability_scores=ability_scores,
            skills=skills,
            classes=classes,
            spells=spells,
            spell_slots=spell_slots,
            equipment=equipment,
            features=features,
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
