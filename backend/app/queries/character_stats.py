"""Small cross-domain reads shared by the attack-resolution queries.

Split out of `app.combat.service` (Fase 8 audit) so `weapon_attack.py` and
`spell_attack.py` don't each keep their own copy.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.catalog.domain import AbilityScore
from app.characters.models import Character, CharacterAbilityScore
from engine.abilities import calculate_modifier


async def character_ability_modifier(
    character_id: uuid.UUID, ability: AbilityScore, db: AsyncSession
) -> int:
    """Return a character's modifier for `ability`, or 0 if the score isn't set."""
    result = await db.execute(
        select(CharacterAbilityScore).where(
            CharacterAbilityScore.character_id == character_id,
            CharacterAbilityScore.ability == ability,
        )
    )
    score = result.scalar_one_or_none()
    if score is None:
        return 0
    return calculate_modifier(score.base_score + score.asi_bonus + score.misc_bonus)


async def character_proficiency_bonus(character_id: uuid.UUID, db: AsyncSession) -> int:
    """Return a character's proficiency bonus, or 0 if the character isn't found."""
    result = await db.execute(select(Character).where(Character.id == character_id))
    character = result.scalar_one_or_none()
    return character.proficiency_bonus if character is not None else 0
