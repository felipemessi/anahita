"""CharacterService orchestrates character sheet creation."""

import uuid
from typing import Protocol

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.campaigns.models import CampaignMember
from app.catalog import service as catalog_service
from app.catalog.domain import AbilityScore
from app.characters.domain import (
    CrossCampaignCatalogReferenceError,
    validate_catalog_reference,
)
from app.characters.models import Character, CharacterAbilityScore, CharacterClass
from app.characters.schemas import CharacterAbilityScoreCreate, CharacterCreate
from engine.abilities import calculate_modifier, calculate_proficiency_bonus
from engine.armor_class import calculate_ac
from engine.hit_points import calculate_max_hp


class _CatalogScopedEntity(Protocol):
    """Structural type for catalog entities checked by `_validate_reference`."""

    is_custom: bool
    campaign_id: uuid.UUID | None


class CharacterService:
    """Orchestrates character creation and catalog-reference validation."""

    async def create_character(
        self, requester_id: uuid.UUID, data: CharacterCreate, db: AsyncSession
    ) -> Character:
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

        await db.commit()
        result = await db.execute(
            select(Character)
            .where(Character.id == character.id)
            .options(
                selectinload(Character.ability_scores),
                selectinload(Character.classes),
            )
        )
        return result.scalar_one()

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
