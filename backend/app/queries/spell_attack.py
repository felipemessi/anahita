"""Resolve a Character's known spell into an attack/save/damage profile.

Cross-domain (characters + catalog), mirrors `app.queries.weapon_attack`.
Shared by `CombatService` (attack resolved as part of `declare_action`) and
`CharacterService`'s standalone attack endpoint (rolled straight from the
sheet, outside of any encounter).
"""

import uuid
from dataclasses import dataclass

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.catalog.domain import AbilityScore, SpellActionType
from app.catalog.models import (
    AbilityScoreDefinition,
    ClassDefinition,
    Spell,
    SpellDamage,
)
from app.characters.models import Character, CharacterSpell
from app.queries.character_stats import (
    character_ability_modifier,
    character_proficiency_bonus,
)


@dataclass(frozen=True)
class SpellAttackProfile:
    """Everything needed to roll a spell's to-hit/save, then its damage.

    `attack_bonus` is the caster's spell attack modifier — meaningful when
    `action_type` is `attack_roll`; still computed either way (matches the
    combat tracker's existing behaviour) but the sheet only shows an
    "Atacar" button for `attack_roll` spells. `save_dc`/`save_ability` are
    set only for `saving_throw` spells — there's nothing for the caster to
    roll there, the target rolls the save. `damage_dice` is `None` for a
    spell with no damage entry at the resolved level (e.g. a pure
    debuff/utility spell) — no ability modifier is added to spell damage,
    unlike weapon damage.
    """

    spell_name: str
    action_type: SpellActionType | None
    attack_bonus: int
    save_dc: int | None
    save_ability: AbilityScore | None
    damage_dice: str | None
    damage_type: str | None


async def resolve_character_spell_attack(
    character_id: uuid.UUID,
    spell_entry_id: uuid.UUID,
    cast_at_level: int | None,
    db: AsyncSession,
) -> SpellAttackProfile:
    """Resolve a Character's known spell into attack bonus + save + damage.

    Attack bonus / save DC: the casting class's spellcasting-ability
    modifier + proficiency bonus, matched by `CharacterSpell.source_class`
    against the character's classes. Damage: looked up from catalog
    `SpellDamage` at `cast_at_level` (slot-scaled) or the character's class
    level (cantrip/character-level-scaled); `None` if the spell has no
    damage entry at all.
    """
    entry_result = await db.execute(
        select(CharacterSpell).where(
            CharacterSpell.id == spell_entry_id,
            CharacterSpell.character_id == character_id,
        )
    )
    entry = entry_result.scalar_one_or_none()
    if entry is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Spell entry not found on the attacker's character",
        )
    spell_result = await db.execute(
        select(Spell)
        .where(Spell.id == entry.spell_id)
        .options(selectinload(Spell.damages).selectinload(SpellDamage.damage_type))
    )
    spell = spell_result.scalar_one_or_none()
    if spell is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Spell not found"
        )

    character_result = await db.execute(
        select(Character)
        .where(Character.id == character_id)
        .options(selectinload(Character.classes))
    )
    character = character_result.scalar_one()
    ability_mod = 0
    caster_level = character.level
    class_def: ClassDefinition | None = None
    if entry.source_class is not None:
        class_result = await db.execute(
            select(ClassDefinition).where(ClassDefinition.index == entry.source_class)
        )
        class_def = class_result.scalar_one_or_none()
        class_entry = next(
            (
                c
                for c in character.classes
                if class_def is not None and c.class_definition_id == class_def.id
            ),
            None,
        )
        if class_def is not None and class_entry is not None:
            caster_level = class_entry.level
            if class_def.spellcasting_ability is not None:
                ability_mod = await character_ability_modifier(
                    character_id, AbilityScore(class_def.spellcasting_ability), db
                )
    proficiency_bonus = await character_proficiency_bonus(character_id, db)
    attack_bonus = ability_mod + proficiency_bonus

    save_dc = None
    save_ability = None
    if spell.action_type == SpellActionType.saving_throw:
        if class_def is not None and class_def.spellcasting_ability is not None:
            save_dc = 8 + proficiency_bonus + ability_mod
        if spell.save_ability_score_id is not None:
            ability_result = await db.execute(
                select(AbilityScoreDefinition).where(
                    AbilityScoreDefinition.id == spell.save_ability_score_id
                )
            )
            ability_def = ability_result.scalar_one_or_none()
            if ability_def is not None and ability_def.index is not None:
                save_ability = AbilityScore(ability_def.index)

    target_level = cast_at_level or spell.level
    damage_row = next(
        (
            d
            for d in spell.damages
            if (d.scaling_type == "slot_level" and d.scaling_key == target_level)
            or (
                d.scaling_type == "character_level"
                and d.scaling_key
                == max((k for k in (1, 5, 11, 17) if k <= caster_level), default=1)
            )
        ),
        None,
    )
    return SpellAttackProfile(
        spell_name=spell.index or "spell",
        action_type=spell.action_type,
        attack_bonus=attack_bonus,
        save_dc=save_dc,
        save_ability=save_ability,
        damage_dice=damage_row.dice_expression if damage_row is not None else None,
        damage_type=(
            damage_row.damage_type.index or "" if damage_row is not None else None
        ),
    )
