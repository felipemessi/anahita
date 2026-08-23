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
    ClassDefinitionI18n,
    ClassLevel,
    ClassLevelFeature,
    Condition,
    DamageType,
    EquipmentCategoryI18n,
    Feature,
    FeatureI18n,
    Item,
    ItemI18n,
    ItemProperty,
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
    SpellClass,
    SpellI18n,
    SubclassDefinition,
    SubclassDefinitionI18n,
    Subrace,
    SubraceI18n,
    SubraceTrait,
    SubraceTraitI18n,
    WeaponDetail,
    WeaponProperty,
    WeaponPropertyI18n,
)
from app.catalog.schemas import (
    ArmorDetailRead,
    ClassDefinitionRead,
    ClassLevelRead,
    ClassLevelResourceRead,
    ClassLevelSpellSlotRead,
    ClassSummary,
    FeaturePrerequisiteRead,
    FeatureRead,
    ItemPropertyRead,
    ItemRead,
    ItemSummary,
    RaceAbilityBonusRead,
    RaceRead,
    RaceSummary,
    RaceTraitRead,
    SpellClassRead,
    SpellRead,
    SpellSummary,
    SubclassRead,
    SubraceRead,
    SubraceTraitRead,
    WeaponDetailRead,
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


#: Eager-load options shared by `list_classes`/`get_class`: full progression
#: (base + subclass `ClassLevel` rows with their features/slots/resources) and
#: subclass-direct features, plus every `Feature`'s prerequisites.
_CLASS_LOAD_OPTIONS = (
    selectinload(ClassDefinition.class_levels)
    .selectinload(ClassLevel.level_features)
    .selectinload(ClassLevelFeature.feature)
    .selectinload(Feature.prerequisites),
    selectinload(ClassDefinition.class_levels).selectinload(ClassLevel.spell_slots),
    selectinload(ClassDefinition.class_levels).selectinload(ClassLevel.resources),
    selectinload(ClassDefinition.subclasses)
    .selectinload(SubclassDefinition.features)
    .selectinload(Feature.prerequisites),
)


async def list_classes(
    session: AsyncSession,
    *,
    include_custom: bool = True,
    campaign_id: uuid.UUID | None = None,
) -> list[ClassDefinition]:
    """Return all class definitions (base rows, eager-loaded progression, untranslated).

    See `list_races` for the `campaign_id` vs. `include_custom` scoping rules.
    """
    stmt = select(ClassDefinition).options(*_CLASS_LOAD_OPTIONS)
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
    """Return a single class definition by ID (untranslated), or None if not found."""
    stmt = (
        select(ClassDefinition)
        .where(ClassDefinition.id == class_id)
        .options(*_CLASS_LOAD_OPTIONS)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def _translate_feature(
    session: AsyncSession, feature: Feature, locale: str
) -> FeatureRead:
    t = await get_translated(
        session, FeatureI18n, FeatureI18n.entity_id, entity_id=feature.id, locale=locale
    )
    return FeatureRead(
        id=feature.id,
        index=feature.index,
        level=feature.level,
        feature_name=t.feature_name if t else "",
        description=t.description if t else "",
        mechanical_effect=feature.mechanical_effect,
        parent_feature_id=feature.parent_feature_id,
        prerequisites=[
            FeaturePrerequisiteRead.model_validate(p) for p in feature.prerequisites
        ],
    )


async def _translate_class_level(
    session: AsyncSession, class_level: ClassLevel, locale: str
) -> ClassLevelRead:
    features = [
        await _translate_feature(session, clf.feature, locale)
        for clf in class_level.level_features
    ]
    return ClassLevelRead(
        id=class_level.id,
        level=class_level.level,
        proficiency_bonus=class_level.proficiency_bonus,
        ability_score_bonuses=class_level.ability_score_bonuses,
        features=features,
        spell_slots=[
            ClassLevelSpellSlotRead.model_validate(s) for s in class_level.spell_slots
        ],
        resources=[
            ClassLevelResourceRead.model_validate(r) for r in class_level.resources
        ],
    )


async def _translate_subclass(
    session: AsyncSession, subclass: SubclassDefinition, locale: str
) -> SubclassRead:
    t = await get_translated(
        session,
        SubclassDefinitionI18n,
        SubclassDefinitionI18n.entity_id,
        entity_id=subclass.id,
        locale=locale,
    )
    features = [
        await _translate_feature(session, feature, locale)
        for feature in subclass.features
    ]
    return SubclassRead(
        id=subclass.id,
        index=subclass.index,
        name=t.name if t else "",
        description=t.description if t else "",
        flavor=t.flavor if t else "",
        is_custom=subclass.is_custom,
        features=features,
    )


async def get_class_translated(
    session: AsyncSession, class_id: uuid.UUID, *, locale: str = "en"
) -> ClassDefinitionRead | None:
    """Return a class by ID with every translatable field resolved for `locale`."""
    cls = await get_class(session, class_id)
    if cls is None:
        return None
    t = await get_translated(
        session,
        ClassDefinitionI18n,
        ClassDefinitionI18n.entity_id,
        entity_id=cls.id,
        locale=locale,
    )
    base_levels = sorted(
        (cl for cl in cls.class_levels if cl.subclass_definition_id is None),
        key=lambda cl: cl.level,
    )
    levels = [
        await _translate_class_level(session, cl, locale) for cl in base_levels
    ]
    subclasses = [
        await _translate_subclass(session, sc, locale) for sc in cls.subclasses
    ]
    return ClassDefinitionRead(
        id=cls.id,
        index=cls.index,
        name=t.name if t else "",
        hit_die=cls.hit_die,
        primary_ability=cls.primary_ability,
        saving_throw_proficiencies=cls.saving_throw_proficiencies,
        is_custom=cls.is_custom,
        levels=levels,
        subclasses=subclasses,
    )


async def list_classes_translated(
    session: AsyncSession,
    *,
    search: str | None = None,
    include_custom: bool = True,
    campaign_id: uuid.UUID | None = None,
    locale: str = "en",
) -> list[ClassSummary]:
    """Return all classes with `name` resolved for `locale`, optionally name-filtered.

    Mirrors `list_races_translated`: class counts are small enough that
    resolving translations per-row here is simpler than a fallback-aware SQL
    join.
    """
    classes = await list_classes(
        session, include_custom=include_custom, campaign_id=campaign_id
    )
    summaries = []
    for cls in classes:
        t = await get_translated(
            session,
            ClassDefinitionI18n,
            ClassDefinitionI18n.entity_id,
            entity_id=cls.id,
            locale=locale,
        )
        summaries.append(
            ClassSummary(
                id=cls.id,
                index=cls.index,
                name=t.name if t else "",
                hit_die=cls.hit_die,
                primary_ability=cls.primary_ability,
                is_custom=cls.is_custom,
            )
        )
    if search:
        needle = search.lower()
        summaries = [s for s in summaries if needle in s.name.lower()]
    summaries.sort(key=lambda s: s.name)
    return summaries


async def list_spells(
    session: AsyncSession,
    *,
    level: int | None = None,
    school: str | None = None,
    include_custom: bool = True,
    campaign_id: uuid.UUID | None = None,
) -> list[Spell]:
    """Return all spells (base rows, eager-loaded classes/school, untranslated).

    `school` filters by the `MagicSchool.index` slug (e.g. `evocation`). See
    `list_races` for the `campaign_id` vs. `include_custom` scoping rules.
    """
    stmt = (
        select(Spell)
        .join(MagicSchool, Spell.magic_school_id == MagicSchool.id)
        .options(
            selectinload(Spell.magic_school),
            selectinload(Spell.classes).selectinload(SpellClass.class_definition),
        )
        .order_by(Spell.level)
    )
    if level is not None:
        stmt = stmt.where(Spell.level == level)
    if school:
        stmt = stmt.where(MagicSchool.index == school)
    if campaign_id is not None:
        stmt = stmt.where(
            or_(Spell.campaign_id.is_(None), Spell.campaign_id == campaign_id)
        )
    elif not include_custom:
        stmt = stmt.where(Spell.is_custom.is_(False))
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_spell(session: AsyncSession, spell_id: uuid.UUID) -> Spell | None:
    """Return a single spell by ID (untranslated), or None if not found."""
    stmt = (
        select(Spell)
        .where(Spell.id == spell_id)
        .options(
            selectinload(Spell.magic_school),
            selectinload(Spell.classes).selectinload(SpellClass.class_definition),
        )
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def _translate_spell_classes(
    session: AsyncSession, spell: Spell, locale: str
) -> list[SpellClassRead]:
    reads = []
    for sc in spell.classes:
        t = await get_translated(
            session,
            ClassDefinitionI18n,
            ClassDefinitionI18n.entity_id,
            entity_id=sc.class_definition_id,
            locale=locale,
        )
        reads.append(
            SpellClassRead(id=sc.class_definition_id, name=t.name if t else "")
        )
    return reads


async def get_spell_translated(
    session: AsyncSession, spell_id: uuid.UUID, *, locale: str = "en"
) -> SpellRead | None:
    """Return a spell by ID with every translatable field resolved for `locale`."""
    spell = await get_spell(session, spell_id)
    if spell is None:
        return None
    t = await get_translated(
        session, SpellI18n, SpellI18n.entity_id, entity_id=spell.id, locale=locale
    )
    return SpellRead(
        id=spell.id,
        index=spell.index,
        name=t.name if t else "",
        level=spell.level,
        school=spell.magic_school.index or "",
        casting_time=spell.casting_time,
        range=spell.range,
        duration=spell.duration,
        components=spell.components,
        ritual=spell.ritual,
        concentration=spell.concentration,
        description=t.description if t else "",
        higher_levels=t.higher_levels if t else None,
        is_custom=spell.is_custom,
        classes=await _translate_spell_classes(session, spell, locale),
    )


async def list_spells_translated(
    session: AsyncSession,
    *,
    search: str | None = None,
    level: int | None = None,
    school: str | None = None,
    include_custom: bool = True,
    campaign_id: uuid.UUID | None = None,
    locale: str = "en",
) -> list[SpellSummary]:
    """Return all spells with `name` resolved for `locale`, optionally name-filtered.

    Mirrors `list_races_translated`: spell counts are small enough (a few
    hundred at most) that resolving translations per-row here is simpler than
    a fallback-aware SQL join.
    """
    spells = await list_spells(
        session,
        level=level,
        school=school,
        include_custom=include_custom,
        campaign_id=campaign_id,
    )
    summaries = []
    for spell in spells:
        t = await get_translated(
            session, SpellI18n, SpellI18n.entity_id, entity_id=spell.id, locale=locale
        )
        summaries.append(
            SpellSummary(
                id=spell.id,
                index=spell.index,
                name=t.name if t else "",
                level=spell.level,
                school=spell.magic_school.index or "",
                ritual=spell.ritual,
                concentration=spell.concentration,
                is_custom=spell.is_custom,
            )
        )
    if search:
        needle = search.lower()
        summaries = [s for s in summaries if needle in s.name.lower()]
    summaries.sort(key=lambda s: (s.level, s.name))
    return summaries


#: Eager-load options shared by `list_items`/`get_item`.
_ITEM_LOAD_OPTIONS = (
    selectinload(Item.weapon_detail).selectinload(WeaponDetail.damage_type),
    selectinload(Item.armor_detail),
    selectinload(Item.properties).selectinload(ItemProperty.weapon_property),
    selectinload(Item.equipment_category),
)


async def list_items(
    session: AsyncSession,
    *,
    item_type: str | None = None,
    include_custom: bool = True,
    campaign_id: uuid.UUID | None = None,
) -> list[Item]:
    """Return all items (base rows, eager-loaded details, untranslated).

    See `list_races` for the `campaign_id` vs. `include_custom` scoping rules.
    """
    stmt = select(Item).options(*_ITEM_LOAD_OPTIONS)
    if item_type:
        stmt = stmt.where(Item.item_type == item_type)
    if campaign_id is not None:
        stmt = stmt.where(
            or_(Item.campaign_id.is_(None), Item.campaign_id == campaign_id)
        )
    elif not include_custom:
        stmt = stmt.where(Item.is_custom.is_(False))
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_item(session: AsyncSession, item_id: uuid.UUID) -> Item | None:
    """Return a single item by ID (untranslated), or None if not found."""
    stmt = select(Item).where(Item.id == item_id).options(*_ITEM_LOAD_OPTIONS)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def _translate_item_properties(
    session: AsyncSession, item: Item, locale: str
) -> list[ItemPropertyRead]:
    reads = []
    for prop in item.properties:
        t = await get_translated(
            session,
            WeaponPropertyI18n,
            WeaponPropertyI18n.entity_id,
            entity_id=prop.weapon_property_id,
            locale=locale,
        )
        reads.append(
            ItemPropertyRead(id=prop.weapon_property_id, name=t.name if t else "")
        )
    return reads


async def get_item_translated(
    session: AsyncSession, item_id: uuid.UUID, *, locale: str = "en"
) -> ItemRead | None:
    """Return an item by ID with every translatable field resolved for `locale`."""
    item = await get_item(session, item_id)
    if item is None:
        return None
    t = await get_translated(
        session, ItemI18n, ItemI18n.entity_id, entity_id=item.id, locale=locale
    )
    category_t = await get_translated(
        session,
        EquipmentCategoryI18n,
        EquipmentCategoryI18n.entity_id,
        entity_id=item.equipment_category_id,
        locale=locale,
    )
    weapon_detail = None
    if item.weapon_detail is not None:
        weapon_detail = WeaponDetailRead(
            id=item.weapon_detail.id,
            damage_dice=item.weapon_detail.damage_dice,
            damage_type=item.weapon_detail.damage_type.index or "",
            weapon_range=item.weapon_detail.weapon_range,
        )
    return ItemRead(
        id=item.id,
        index=item.index,
        name=t.name if t else "",
        item_type=item.item_type,
        equipment_category=category_t.name if category_t else "",
        rarity=item.rarity,
        weight=item.weight,
        cost=item.cost,
        description=t.description if t else "",
        is_custom=item.is_custom,
        properties=await _translate_item_properties(session, item, locale),
        weapon_detail=weapon_detail,
        armor_detail=(
            ArmorDetailRead.model_validate(item.armor_detail)
            if item.armor_detail is not None
            else None
        ),
    )


async def list_items_translated(
    session: AsyncSession,
    *,
    search: str | None = None,
    item_type: str | None = None,
    include_custom: bool = True,
    campaign_id: uuid.UUID | None = None,
    locale: str = "en",
) -> list[ItemSummary]:
    """Return all items with `name` resolved for `locale`, optionally name-filtered.

    Mirrors `list_races_translated`: item counts are small enough that
    resolving translations per-row here is simpler than a fallback-aware SQL
    join.
    """
    items = await list_items(
        session,
        item_type=item_type,
        include_custom=include_custom,
        campaign_id=campaign_id,
    )
    summaries = []
    for item in items:
        t = await get_translated(
            session, ItemI18n, ItemI18n.entity_id, entity_id=item.id, locale=locale
        )
        summaries.append(
            ItemSummary(
                id=item.id,
                index=item.index,
                name=t.name if t else "",
                item_type=item.item_type,
                rarity=item.rarity,
                weight=item.weight,
                cost=item.cost,
                is_custom=item.is_custom,
            )
        )
    if search:
        needle = search.lower()
        summaries = [s for s in summaries if needle in s.name.lower()]
    summaries.sort(key=lambda s: s.name)
    return summaries


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
