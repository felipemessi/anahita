"""CharacterService orchestrates character sheet creation and reads."""

import uuid
from typing import Protocol

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.campaigns.domain import CampaignRole
from app.campaigns.models import CampaignMember
from app.catalog import service as catalog_service
from app.catalog.domain import AbilityScore
from app.characters.domain import (
    SKILL_ABILITY,
    CrossCampaignCatalogReferenceError,
    Skill,
    validate_catalog_reference,
)
from app.characters.models import (
    Character,
    CharacterAbilityScore,
    CharacterClass,
    CharacterSkill,
)
from app.characters.schemas import (
    CharacterAbilityScoreCreate,
    CharacterAbilityScoreRead,
    CharacterClassRead,
    CharacterCreate,
    CharacterRead,
    CharacterSkillRead,
)
from engine.abilities import (
    calculate_modifier,
    calculate_proficiency_bonus,
    calculate_skill_bonus,
)
from engine.armor_class import calculate_ac
from engine.hit_points import calculate_max_hp

_CHARACTER_LOAD_OPTIONS = (
    selectinload(Character.ability_scores),
    selectinload(Character.skills),
    selectinload(Character.classes),
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
        return self._to_read(character)

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
        """Reload a freshly-created character with relationships, as a read schema."""
        result = await db.execute(
            select(Character)
            .where(Character.id == character_id)
            .options(*_CHARACTER_LOAD_OPTIONS)
        )
        return self._to_read(result.scalar_one())

    def _to_read(self, character: Character) -> CharacterRead:
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
                detail="Cannot create a character for someone else's membership",
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
