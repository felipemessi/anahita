"""Catalog service — read-only queries for SRD reference data."""

import uuid

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute, selectinload

from app.catalog.mixins import CatalogI18nMixin
from app.catalog.models import (
    AbilityScoreDefinition,
    Alignment,
    ClassDefinition,
    Condition,
    DamageType,
    Item,
    Language,
    MagicSchool,
    Proficiency,
    ProficiencyClass,
    ProficiencyRace,
    Race,
    RaceI18n,
    RaceTrait,
    RaceTraitI18n,
    SkillDefinition,
    Spell,
    Subrace,
    SubraceI18n,
    SubraceTrait,
    SubraceTraitI18n,
    WeaponProperty,
)
from app.catalog.schemas import (
    RaceAbilityBonusRead,
    RaceRead,
    RaceSummary,
    RaceTraitRead,
    SubraceRead,
    SubraceTraitRead,
)


async def get_translated[T: CatalogI18nMixin](
    session: AsyncSession,
    i18n_model: type[T],
    entity_fk: InstrumentedAttribute[uuid.UUID],
    *,
    entity_id: uuid.UUID,
    locale: str,
) -> T | None:
    """Return the `_i18n` row for `entity_id` in `locale`, falling back to `en`.

    Generic helper reused by every catalog category that follows the `_i18n`
    convention (see `app.catalog.mixins`): pass the `_i18n` model class and its
    `entity_id` FK column, and it resolves the translation with fallback.
    """
    stmt = select(i18n_model).where(entity_fk == entity_id, i18n_model.locale == locale)
    result = await session.execute(stmt)
    row = result.scalar_one_or_none()
    if row is not None or locale == "en":
        return row

    fallback_stmt = select(i18n_model).where(
        entity_fk == entity_id, i18n_model.locale == "en"
    )
    fallback_result = await session.execute(fallback_stmt)
    return fallback_result.scalar_one_or_none()


async def list_races(
    session: AsyncSession,
    *,
    include_custom: bool = True,
    campaign_id: uuid.UUID | None = None,
) -> list[Race]:
    """Return all races (base rows, eager-loaded traits/subraces, untranslated).

    When `campaign_id` is given, scopes the listing to SRD content
    (`campaign_id IS NULL`) plus homebrew belonging to that campaign — never
    homebrew from another campaign. `include_custom` is ignored in that case;
    it only controls whether *any* homebrew is included when no campaign is
    given (e.g. an unauthenticated/global catalog browse).
    """
    stmt = select(Race).options(
        selectinload(Race.traits),
        selectinload(Race.ability_bonuses),
        selectinload(Race.subraces).selectinload(Subrace.traits),
        selectinload(Race.subraces).selectinload(Subrace.ability_bonuses),
    )
    if campaign_id is not None:
        stmt = stmt.where(
            or_(Race.campaign_id.is_(None), Race.campaign_id == campaign_id)
        )
    elif not include_custom:
        stmt = stmt.where(Race.is_custom.is_(False))
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_race(session: AsyncSession, race_id: uuid.UUID) -> Race | None:
    """Return a single race by ID (untranslated), or None if not found."""
    stmt = (
        select(Race)
        .where(Race.id == race_id)
        .options(
            selectinload(Race.traits),
            selectinload(Race.ability_bonuses),
            selectinload(Race.subraces).selectinload(Subrace.traits),
            selectinload(Race.subraces).selectinload(Subrace.ability_bonuses),
        )
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def _translate_race_trait(
    session: AsyncSession, trait: RaceTrait, locale: str
) -> RaceTraitRead:
    t = await get_translated(
        session,
        RaceTraitI18n,
        RaceTraitI18n.entity_id,
        entity_id=trait.id,
        locale=locale,
    )
    return RaceTraitRead(
        id=trait.id,
        trait_name=t.trait_name if t else "",
        description=t.description if t else "",
        mechanical_effect=trait.mechanical_effect,
    )


async def _translate_subrace_trait(
    session: AsyncSession, trait: SubraceTrait, locale: str
) -> SubraceTraitRead:
    t = await get_translated(
        session,
        SubraceTraitI18n,
        SubraceTraitI18n.entity_id,
        entity_id=trait.id,
        locale=locale,
    )
    return SubraceTraitRead(
        id=trait.id,
        trait_name=t.trait_name if t else "",
        description=t.description if t else "",
        mechanical_effect=trait.mechanical_effect,
    )


async def _translate_subrace(
    session: AsyncSession, subrace: Subrace, locale: str
) -> SubraceRead:
    t = await get_translated(
        session, SubraceI18n, SubraceI18n.entity_id, entity_id=subrace.id, locale=locale
    )
    traits = [
        await _translate_subrace_trait(session, trait, locale)
        for trait in subrace.traits
    ]
    return SubraceRead(
        id=subrace.id,
        index=subrace.index,
        name=t.name if t else "",
        description=t.description if t else "",
        traits=traits,
        ability_bonuses=[
            RaceAbilityBonusRead.model_validate(ab) for ab in subrace.ability_bonuses
        ],
    )


async def get_race_translated(
    session: AsyncSession, race_id: uuid.UUID, *, locale: str = "en"
) -> RaceRead | None:
    """Return a race by ID with every translatable field resolved for `locale`."""
    race = await get_race(session, race_id)
    if race is None:
        return None
    t = await get_translated(
        session, RaceI18n, RaceI18n.entity_id, entity_id=race.id, locale=locale
    )
    traits = [
        await _translate_race_trait(session, trait, locale) for trait in race.traits
    ]
    subraces = [
        await _translate_subrace(session, subrace, locale) for subrace in race.subraces
    ]
    return RaceRead(
        id=race.id,
        index=race.index,
        name=t.name if t else "",
        description=t.description if t else "",
        age=t.age if t else "",
        alignment_desc=t.alignment_desc if t else "",
        size_description=t.size_description if t else "",
        language_desc=t.language_desc if t else "",
        speed=race.speed,
        size=race.size,
        darkvision_range=race.darkvision_range,
        is_custom=race.is_custom,
        traits=traits,
        subraces=subraces,
        ability_bonuses=[
            RaceAbilityBonusRead.model_validate(ab) for ab in race.ability_bonuses
        ],
    )


async def list_races_translated(
    session: AsyncSession,
    *,
    search: str | None = None,
    include_custom: bool = True,
    campaign_id: uuid.UUID | None = None,
    locale: str = "en",
) -> list[RaceSummary]:
    """Return all races with `name` resolved for `locale`, optionally name-filtered.

    Race counts are small (a few dozen at most, even with homebrew), so
    resolving translations per-row here is simpler than a fallback-aware SQL
    join and cheap enough in practice.
    """
    races = await list_races(
        session, include_custom=include_custom, campaign_id=campaign_id
    )
    summaries = []
    for race in races:
        t = await get_translated(
            session, RaceI18n, RaceI18n.entity_id, entity_id=race.id, locale=locale
        )
        summaries.append(
            RaceSummary(
                id=race.id,
                index=race.index,
                name=t.name if t else "",
                speed=race.speed,
                size=race.size,
                darkvision_range=race.darkvision_range,
                is_custom=race.is_custom,
            )
        )
    if search:
        needle = search.lower()
        summaries = [s for s in summaries if needle in s.name.lower()]
    summaries.sort(key=lambda s: s.name)
    return summaries


async def list_classes(
    session: AsyncSession,
    *,
    search: str | None = None,
    include_custom: bool = True,
    campaign_id: uuid.UUID | None = None,
) -> list[ClassDefinition]:
    """Return all class definitions, optionally filtered by name substring.

    See `list_races` for the `campaign_id` vs. `include_custom` scoping rules.
    """
    stmt = (
        select(ClassDefinition)
        .options(
            selectinload(ClassDefinition.level_features),
            selectinload(ClassDefinition.subclasses),
        )
        .order_by(ClassDefinition.name)
    )
    if search:
        stmt = stmt.where(ClassDefinition.name.ilike(f"%{search}%"))
    if campaign_id is not None:
        stmt = stmt.where(
            or_(
                ClassDefinition.campaign_id.is_(None),
                ClassDefinition.campaign_id == campaign_id,
            )
        )
    elif not include_custom:
        stmt = stmt.where(ClassDefinition.is_custom.is_(False))
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_class(
    session: AsyncSession, class_id: uuid.UUID
) -> ClassDefinition | None:
    """Return a single class definition by ID, or None if not found."""
    stmt = (
        select(ClassDefinition)
        .where(ClassDefinition.id == class_id)
        .options(
            selectinload(ClassDefinition.level_features),
            selectinload(ClassDefinition.subclasses),
        )
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def list_spells(
    session: AsyncSession,
    *,
    search: str | None = None,
    level: int | None = None,
    school: str | None = None,
) -> list[Spell]:
    """Return all spells, optionally filtered by name, level, or school."""
    stmt = select(Spell).order_by(Spell.level, Spell.name)
    if search:
        stmt = stmt.where(Spell.name.ilike(f"%{search}%"))
    if level is not None:
        stmt = stmt.where(Spell.level == level)
    if school:
        stmt = stmt.where(Spell.school == school)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_spell(session: AsyncSession, spell_id: uuid.UUID) -> Spell | None:
    """Return a single spell by ID, or None if not found."""
    result = await session.execute(select(Spell).where(Spell.id == spell_id))
    return result.scalar_one_or_none()


async def list_items(
    session: AsyncSession,
    *,
    search: str | None = None,
    item_type: str | None = None,
) -> list[Item]:
    """Return all items, optionally filtered by name substring or type."""
    stmt = (
        select(Item)
        .options(
            selectinload(Item.weapon_detail),
            selectinload(Item.armor_detail),
        )
        .order_by(Item.name)
    )
    if search:
        stmt = stmt.where(Item.name.ilike(f"%{search}%"))
    if item_type:
        stmt = stmt.where(Item.item_type == item_type)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_item(session: AsyncSession, item_id: uuid.UUID) -> Item | None:
    """Return a single item by ID, or None if not found."""
    stmt = (
        select(Item)
        .where(Item.id == item_id)
        .options(
            selectinload(Item.weapon_detail),
            selectinload(Item.armor_detail),
        )
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


# --- Fixed vocabulary (SRD 2014 §7.4.1) -------------------------------------
#
# Read-only: this fixed vocabulary is seeded, not created via API. Translated
# text is resolved separately via `get_translated` (see above) — callers pass
# the matching `_i18n` model and its `entity_id` column.


async def list_ability_scores(session: AsyncSession) -> list[AbilityScoreDefinition]:
    """Return all ability score definitions."""
    result = await session.execute(
        select(AbilityScoreDefinition).order_by(AbilityScoreDefinition.index)
    )
    return list(result.scalars().all())


async def get_ability_score(
    session: AsyncSession, entity_id: uuid.UUID
) -> AbilityScoreDefinition | None:
    """Return a single ability score definition by ID, or None if not found."""
    result = await session.execute(
        select(AbilityScoreDefinition).where(AbilityScoreDefinition.id == entity_id)
    )
    return result.scalar_one_or_none()


async def list_skills(session: AsyncSession) -> list[SkillDefinition]:
    """Return all skill definitions."""
    result = await session.execute(
        select(SkillDefinition).order_by(SkillDefinition.index)
    )
    return list(result.scalars().all())


async def get_skill(
    session: AsyncSession, entity_id: uuid.UUID
) -> SkillDefinition | None:
    """Return a single skill definition by ID, or None if not found."""
    result = await session.execute(
        select(SkillDefinition).where(SkillDefinition.id == entity_id)
    )
    return result.scalar_one_or_none()


async def list_alignments(session: AsyncSession) -> list[Alignment]:
    """Return all alignments."""
    result = await session.execute(select(Alignment).order_by(Alignment.index))
    return list(result.scalars().all())


async def get_alignment(
    session: AsyncSession, entity_id: uuid.UUID
) -> Alignment | None:
    """Return a single alignment by ID, or None if not found."""
    result = await session.execute(select(Alignment).where(Alignment.id == entity_id))
    return result.scalar_one_or_none()


async def list_conditions(session: AsyncSession) -> list[Condition]:
    """Return all conditions."""
    result = await session.execute(select(Condition).order_by(Condition.index))
    return list(result.scalars().all())


async def get_condition(
    session: AsyncSession, entity_id: uuid.UUID
) -> Condition | None:
    """Return a single condition by ID, or None if not found."""
    result = await session.execute(select(Condition).where(Condition.id == entity_id))
    return result.scalar_one_or_none()


async def list_damage_types(session: AsyncSession) -> list[DamageType]:
    """Return all damage types."""
    result = await session.execute(select(DamageType).order_by(DamageType.index))
    return list(result.scalars().all())


async def get_damage_type(
    session: AsyncSession, entity_id: uuid.UUID
) -> DamageType | None:
    """Return a single damage type by ID, or None if not found."""
    result = await session.execute(select(DamageType).where(DamageType.id == entity_id))
    return result.scalar_one_or_none()


async def list_magic_schools(session: AsyncSession) -> list[MagicSchool]:
    """Return all schools of magic."""
    result = await session.execute(select(MagicSchool).order_by(MagicSchool.index))
    return list(result.scalars().all())


async def get_magic_school(
    session: AsyncSession, entity_id: uuid.UUID
) -> MagicSchool | None:
    """Return a single school of magic by ID, or None if not found."""
    result = await session.execute(
        select(MagicSchool).where(MagicSchool.id == entity_id)
    )
    return result.scalar_one_or_none()


async def list_languages(session: AsyncSession) -> list[Language]:
    """Return all languages."""
    result = await session.execute(select(Language).order_by(Language.index))
    return list(result.scalars().all())


async def get_language(session: AsyncSession, entity_id: uuid.UUID) -> Language | None:
    """Return a single language by ID, or None if not found."""
    result = await session.execute(select(Language).where(Language.id == entity_id))
    return result.scalar_one_or_none()


async def list_weapon_properties(session: AsyncSession) -> list[WeaponProperty]:
    """Return all weapon properties."""
    result = await session.execute(
        select(WeaponProperty).order_by(WeaponProperty.index)
    )
    return list(result.scalars().all())


async def get_weapon_property(
    session: AsyncSession, entity_id: uuid.UUID
) -> WeaponProperty | None:
    """Return a single weapon property by ID, or None if not found."""
    result = await session.execute(
        select(WeaponProperty).where(WeaponProperty.id == entity_id)
    )
    return result.scalar_one_or_none()


# --- Proficiencies (SRD 2014 §7.4.3) ----------------------------------------


async def list_proficiencies(session: AsyncSession) -> list[Proficiency]:
    """Return all proficiencies."""
    result = await session.execute(select(Proficiency).order_by(Proficiency.index))
    return list(result.scalars().all())


async def get_proficiency(
    session: AsyncSession, entity_id: uuid.UUID
) -> Proficiency | None:
    """Return a single proficiency by ID, or None if not found."""
    result = await session.execute(
        select(Proficiency).where(Proficiency.id == entity_id)
    )
    return result.scalar_one_or_none()


async def list_proficiencies_for_class(
    session: AsyncSession, class_definition_id: uuid.UUID
) -> list[Proficiency]:
    """Return the proficiencies a ClassDefinition grants by default."""
    stmt = (
        select(Proficiency)
        .join(ProficiencyClass, ProficiencyClass.proficiency_id == Proficiency.id)
        .where(ProficiencyClass.class_definition_id == class_definition_id)
        .order_by(Proficiency.index)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def list_proficiencies_for_race(
    session: AsyncSession, race_id: uuid.UUID
) -> list[Proficiency]:
    """Return the proficiencies a Race grants by default."""
    stmt = (
        select(Proficiency)
        .join(ProficiencyRace, ProficiencyRace.proficiency_id == Proficiency.id)
        .where(ProficiencyRace.race_id == race_id)
        .order_by(Proficiency.index)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())
