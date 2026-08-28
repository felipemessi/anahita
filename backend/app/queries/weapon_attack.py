"""Resolve a Character's equipped weapon into an attack profile.

Cross-domain (characters + catalog): reads `CharacterEquipment`/`Item`/
`WeaponDetail` plus the character's classes/proficiencies/ability scores.
Shared by `CombatService` (attack resolved as part of `declare_action`) and
`CharacterService`'s standalone attack endpoint (attack rolled straight
from the sheet, outside of any encounter) — see backlog "Quando eu tenho
uma arma equipada, eu devo ser capaz de atacar com ela".
"""

import uuid
from dataclasses import dataclass

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.catalog.domain import AbilityScore
from app.catalog.models import (
    EquipmentCategory,
    Item,
    ItemProperty,
    Proficiency,
    ProficiencyClass,
    WeaponDetail,
)
from app.characters.models import CharacterClass, CharacterEquipment
from app.queries.character_stats import (
    character_ability_modifier,
    character_proficiency_bonus,
)


@dataclass(frozen=True)
class WeaponAttackProfile:
    """Everything needed to roll an attack, then damage, with an equipped weapon."""

    weapon_name: str
    ability: AbilityScore
    attack_bonus: int
    damage_dice: str
    damage_bonus: int
    damage_type: str
    proficient: bool


def _weapon_name_tokens(index: str) -> frozenset[str]:
    """Hyphen-split `index` into naively-singularized tokens, order-independent.

    Used to match a specific-weapon `Proficiency.index` (e.g.
    `"hand-crossbows"`) against an `Item.index` that names the same weapon
    in a different word order (e.g. `"crossbow-hand"`) — see
    `_is_weapon_proficient`. Naive `-s` stripping is reliable in this
    domain (weapon names), not a general English depluralizer.
    """
    return frozenset(
        token[:-1] if token.endswith("s") else token
        for token in index.split("-")
        if token
    )


async def is_weapon_proficient(
    character_id: uuid.UUID, item: Item, db: AsyncSession
) -> bool:
    """Whether any of the character's classes grants proficiency with `item`.

    Two ways a class grants it (Fase 8 audit): the broad
    `simple-weapons`/`martial-weapons` category (matched against
    `WeaponDetail.weapon_category`), or a specific named weapon (e.g.
    Rogue's "Longswords") — those SRD entries have no structured
    equipment-category reference, so they're matched by comparing
    singularized, hyphen-token sets against `item.index` (e.g.
    `"hand-crossbows"` -> `{"hand", "crossbow"}` matches item index
    `"crossbow-hand"` -> `{"crossbow", "hand"}`).
    """
    classes_result = await db.execute(
        select(CharacterClass.class_definition_id).where(
            CharacterClass.character_id == character_id
        )
    )
    class_ids = list(classes_result.scalars().all())
    if not class_ids:
        return False

    result = await db.execute(
        select(Proficiency.proficiency_type, Proficiency.index, EquipmentCategory.index)
        .join(ProficiencyClass, ProficiencyClass.proficiency_id == Proficiency.id)
        .outerjoin(
            EquipmentCategory, EquipmentCategory.id == Proficiency.equipment_category_id
        )
        .where(ProficiencyClass.class_definition_id.in_(class_ids))
    )
    weapon_category = (
        item.weapon_detail.weapon_category if item.weapon_detail is not None else None
    )
    item_tokens = _weapon_name_tokens(item.index or "")
    for proficiency_type, prof_index, equipment_category_index in result.all():
        if (
            proficiency_type == "weapon"
            and weapon_category is not None
            and equipment_category_index == f"{weapon_category.value}-weapons"
        ):
            return True
        if (
            proficiency_type == "other"
            and item_tokens
            and _weapon_name_tokens(prof_index or "") == item_tokens
        ):
            return True
    return False


async def resolve_character_weapon_attack(
    character_id: uuid.UUID, equipment_id: uuid.UUID, db: AsyncSession
) -> WeaponAttackProfile:
    """Resolve a Character's equipped weapon into attack bonus + damage.

    Ability used: DEX for ranged or finesse weapons, STR otherwise — for
    finesse specifically the PHB lets the player pick either; this always
    picks DEX (the common choice in play), a documented simplification.
    Proficiency is resolved by `is_weapon_proficient` and only adds the
    proficiency bonus when the character actually has it.
    """
    result = await db.execute(
        select(CharacterEquipment).where(
            CharacterEquipment.id == equipment_id,
            CharacterEquipment.character_id == character_id,
        )
    )
    equipment = result.scalar_one_or_none()
    if equipment is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Equipment entry not found on the attacker's character",
        )
    item_result = await db.execute(
        select(Item)
        .where(Item.id == equipment.item_id)
        .options(
            selectinload(Item.weapon_detail).selectinload(WeaponDetail.damage_type),
            selectinload(Item.properties).selectinload(ItemProperty.weapon_property),
        )
    )
    item = item_result.scalar_one_or_none()
    if item is None or item.weapon_detail is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Selected equipment is not a weapon",
        )
    if not equipment.equipped:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Weapon must be equipped to attack with it",
        )

    has_finesse = any(p.weapon_property.index == "finesse" for p in item.properties)
    ability = (
        AbilityScore.dex
        if item.weapon_detail.weapon_range == "Ranged" or has_finesse
        else AbilityScore.str
    )
    ability_mod = await character_ability_modifier(character_id, ability, db)
    proficient = await is_weapon_proficient(character_id, item, db)
    proficiency_bonus = (
        await character_proficiency_bonus(character_id, db) if proficient else 0
    )
    return WeaponAttackProfile(
        weapon_name=item.index or "weapon",
        ability=ability,
        attack_bonus=ability_mod + proficiency_bonus,
        damage_dice=item.weapon_detail.damage_dice,
        damage_bonus=ability_mod,
        damage_type=item.weapon_detail.damage_type.index or "",
        proficient=proficient,
    )
