"""Catalog service — read-only queries plus homebrew creation for the SRD catalog."""

import uuid

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute, selectinload

from app.catalog.domain import validate_custom_campaign_scope
from app.catalog.mixins import CatalogI18nMixin
from app.catalog.models import (
    AbilityScoreDefinition,
    Alignment,
    Background,
    BackgroundEquipment,
    BackgroundFeature,
    BackgroundFeatureI18n,
    BackgroundI18n,
    BackgroundProficiency,
    ClassDefinition,
    ClassDefinitionI18n,
    ClassLevel,
    ClassLevelFeature,
    Condition,
    DamageType,
    EquipmentCategory,
    EquipmentCategoryI18n,
    Feat,
    FeatI18n,
    Feature,
    FeatureI18n,
    Item,
    ItemI18n,
    ItemProperty,
    Language,
    MagicItem,
    MagicItemI18n,
    MagicSchool,
    Monster,
    MonsterAction,
    MonsterActionDamage,
    MonsterConditionImmunity,
    MonsterDamageModifier,
    MonsterI18n,
    MonsterLegendaryAction,
    MonsterLegendaryActionDamage,
    MonsterProficiency,
    MonsterReaction,
    MonsterReactionDamage,
    MonsterSpecialAbility,
    MonsterSpecialAbilityDamage,
    Proficiency,
    ProficiencyClass,
    ProficiencyRace,
    Race,
    RaceI18n,
    RaceTrait,
    RaceTraitI18n,
    Rule,
    RuleI18n,
    RuleRuleSection,
    RuleSection,
    RuleSectionI18n,
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
    BackgroundEquipmentRead,
    BackgroundFeatureRead,
    BackgroundRead,
    BackgroundSummary,
    ClassDefinitionCreate,
    ClassDefinitionRead,
    ClassLevelRead,
    ClassLevelResourceRead,
    ClassLevelSpellSlotRead,
    ClassSummary,
    FeatPrerequisiteRead,
    FeatRead,
    FeatSummary,
    FeaturePrerequisiteRead,
    FeatureRead,
    ItemCreate,
    ItemPropertyRead,
    ItemRead,
    ItemSummary,
    MagicItemRead,
    MagicItemSummary,
    MonsterActionDamageRead,
    MonsterActionRead,
    MonsterArmorClassRead,
    MonsterConditionImmunityRead,
    MonsterCreate,
    MonsterDamageModifierRead,
    MonsterProficiencyRead,
    MonsterRead,
    MonsterSenseRead,
    MonsterSpeedRead,
    MonsterSummary,
    ProficiencyRead,
    RaceAbilityBonusRead,
    RaceCreate,
    RaceRead,
    RaceSummary,
    RaceTraitRead,
    RuleRead,
    RuleSectionRead,
    RuleSummary,
    SpellClassRead,
    SpellCreate,
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


#: Eager-load options shared by `list_magic_items`/`get_magic_item`.
_MAGIC_ITEM_LOAD_OPTIONS = (
    selectinload(MagicItem.equipment_category),
    selectinload(MagicItem.variants),
)


async def list_magic_items(
    session: AsyncSession,
    *,
    include_custom: bool = True,
    campaign_id: uuid.UUID | None = None,
) -> list[MagicItem]:
    """Return all magic items (base rows, eager-loaded variants, untranslated).

    See `list_races` for the `campaign_id` vs. `include_custom` scoping rules.
    """
    stmt = select(MagicItem).options(*_MAGIC_ITEM_LOAD_OPTIONS)
    if campaign_id is not None:
        stmt = stmt.where(
            or_(MagicItem.campaign_id.is_(None), MagicItem.campaign_id == campaign_id)
        )
    elif not include_custom:
        stmt = stmt.where(MagicItem.is_custom.is_(False))
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_magic_item(
    session: AsyncSession, magic_item_id: uuid.UUID
) -> MagicItem | None:
    """Return a single magic item by ID (untranslated), or None if not found."""
    stmt = (
        select(MagicItem)
        .where(MagicItem.id == magic_item_id)
        .options(*_MAGIC_ITEM_LOAD_OPTIONS)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_magic_item_translated(
    session: AsyncSession, magic_item_id: uuid.UUID, *, locale: str = "en"
) -> MagicItemRead | None:
    """Return a magic item by ID with every translatable field resolved for `locale`."""
    magic_item = await get_magic_item(session, magic_item_id)
    if magic_item is None:
        return None
    t = await get_translated(
        session,
        MagicItemI18n,
        MagicItemI18n.entity_id,
        entity_id=magic_item.id,
        locale=locale,
    )
    category_t = await get_translated(
        session,
        EquipmentCategoryI18n,
        EquipmentCategoryI18n.entity_id,
        entity_id=magic_item.equipment_category_id,
        locale=locale,
    )
    variants = []
    for variant in magic_item.variants:
        vt = await get_translated(
            session,
            MagicItemI18n,
            MagicItemI18n.entity_id,
            entity_id=variant.id,
            locale=locale,
        )
        variants.append(
            MagicItemSummary(
                id=variant.id,
                index=variant.index,
                name=vt.name if vt else "",
                rarity=variant.rarity,
                is_variant=variant.is_variant,
                variant_of_id=variant.variant_of_id,
                is_custom=variant.is_custom,
            )
        )
    return MagicItemRead(
        id=magic_item.id,
        index=magic_item.index,
        name=t.name if t else "",
        description=t.description if t else "",
        equipment_category=category_t.name if category_t else "",
        rarity=magic_item.rarity,
        is_custom=magic_item.is_custom,
        is_variant=magic_item.is_variant,
        variant_of_id=magic_item.variant_of_id,
        variants=variants,
    )


async def list_magic_items_translated(
    session: AsyncSession,
    *,
    search: str | None = None,
    include_custom: bool = True,
    campaign_id: uuid.UUID | None = None,
    locale: str = "en",
) -> list[MagicItemSummary]:
    """Return magic items with `name` resolved for `locale`, optionally name-filtered.

    Mirrors `list_races_translated`: magic item counts are small enough that
    resolving translations per-row here is simpler than a fallback-aware SQL
    join.
    """
    magic_items = await list_magic_items(
        session, include_custom=include_custom, campaign_id=campaign_id
    )
    summaries = []
    for magic_item in magic_items:
        t = await get_translated(
            session,
            MagicItemI18n,
            MagicItemI18n.entity_id,
            entity_id=magic_item.id,
            locale=locale,
        )
        summaries.append(
            MagicItemSummary(
                id=magic_item.id,
                index=magic_item.index,
                name=t.name if t else "",
                rarity=magic_item.rarity,
                is_variant=magic_item.is_variant,
                variant_of_id=magic_item.variant_of_id,
                is_custom=magic_item.is_custom,
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


# --- Backgrounds and Feats (SRD 2014 §7.4.7) --------------------------------

#: Eager-load options shared by `list_backgrounds`/`get_background`.
_BACKGROUND_LOAD_OPTIONS = (
    selectinload(Background.proficiencies).selectinload(BackgroundProficiency.proficiency),
    selectinload(Background.equipment).selectinload(BackgroundEquipment.item),
    selectinload(Background.feature),
)


async def list_backgrounds(
    session: AsyncSession,
    *,
    include_custom: bool = True,
    campaign_id: uuid.UUID | None = None,
) -> list[Background]:
    """Return all backgrounds (base rows, eager-loaded grants, untranslated).

    See `list_races` for the `campaign_id` vs. `include_custom` scoping rules.
    """
    stmt = select(Background).options(*_BACKGROUND_LOAD_OPTIONS)
    if campaign_id is not None:
        stmt = stmt.where(
            or_(Background.campaign_id.is_(None), Background.campaign_id == campaign_id)
        )
    elif not include_custom:
        stmt = stmt.where(Background.is_custom.is_(False))
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_background(
    session: AsyncSession, background_id: uuid.UUID
) -> Background | None:
    """Return a single background by ID (untranslated), or None if not found."""
    stmt = (
        select(Background)
        .where(Background.id == background_id)
        .options(*_BACKGROUND_LOAD_OPTIONS)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def _translate_background_equipment(
    session: AsyncSession, grant: BackgroundEquipment, locale: str
) -> BackgroundEquipmentRead:
    t = await get_translated(
        session, ItemI18n, ItemI18n.entity_id, entity_id=grant.item_id, locale=locale
    )
    return BackgroundEquipmentRead(
        id=grant.id,
        item_id=grant.item_id,
        item_name=t.name if t else "",
        quantity=grant.quantity,
    )


async def _translate_background_feature(
    session: AsyncSession, feature: BackgroundFeature, locale: str
) -> BackgroundFeatureRead:
    t = await get_translated(
        session,
        BackgroundFeatureI18n,
        BackgroundFeatureI18n.entity_id,
        entity_id=feature.id,
        locale=locale,
    )
    return BackgroundFeatureRead(
        id=feature.id,
        feature_name=t.feature_name if t else "",
        description=t.description if t else "",
    )


async def get_background_translated(
    session: AsyncSession, background_id: uuid.UUID, *, locale: str = "en"
) -> BackgroundRead | None:
    """Return a background by ID with every translatable field resolved for `locale`."""
    background = await get_background(session, background_id)
    if background is None:
        return None
    t = await get_translated(
        session,
        BackgroundI18n,
        BackgroundI18n.entity_id,
        entity_id=background.id,
        locale=locale,
    )
    equipment = [
        await _translate_background_equipment(session, grant, locale)
        for grant in background.equipment
    ]
    feature = (
        await _translate_background_feature(session, background.feature, locale)
        if background.feature is not None
        else None
    )
    return BackgroundRead(
        id=background.id,
        index=background.index,
        name=t.name if t else "",
        personality_traits=t.personality_traits if t else "",
        ideals=t.ideals if t else "",
        bonds=t.bonds if t else "",
        flaws=t.flaws if t else "",
        is_custom=background.is_custom,
        proficiencies=[
            ProficiencyRead.model_validate(bp.proficiency)
            for bp in background.proficiencies
        ],
        equipment=equipment,
        feature=feature,
    )


async def list_backgrounds_translated(
    session: AsyncSession,
    *,
    search: str | None = None,
    include_custom: bool = True,
    campaign_id: uuid.UUID | None = None,
    locale: str = "en",
) -> list[BackgroundSummary]:
    """Return backgrounds with `name` resolved for `locale`, optionally name-filtered.

    Mirrors `list_races_translated`: background counts are small enough that
    resolving translations per-row here is simpler than a fallback-aware SQL
    join.
    """
    backgrounds = await list_backgrounds(
        session, include_custom=include_custom, campaign_id=campaign_id
    )
    summaries = []
    for background in backgrounds:
        t = await get_translated(
            session,
            BackgroundI18n,
            BackgroundI18n.entity_id,
            entity_id=background.id,
            locale=locale,
        )
        summaries.append(
            BackgroundSummary(
                id=background.id,
                index=background.index,
                name=t.name if t else "",
                is_custom=background.is_custom,
            )
        )
    if search:
        needle = search.lower()
        summaries = [s for s in summaries if needle in s.name.lower()]
    summaries.sort(key=lambda s: s.name)
    return summaries


async def list_feats(
    session: AsyncSession,
    *,
    include_custom: bool = True,
    campaign_id: uuid.UUID | None = None,
) -> list[Feat]:
    """Return all feats (base rows, eager-loaded prerequisites, untranslated).

    See `list_races` for the `campaign_id` vs. `include_custom` scoping rules.
    """
    stmt = select(Feat).options(selectinload(Feat.prerequisites))
    if campaign_id is not None:
        stmt = stmt.where(
            or_(Feat.campaign_id.is_(None), Feat.campaign_id == campaign_id)
        )
    elif not include_custom:
        stmt = stmt.where(Feat.is_custom.is_(False))
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_feat(session: AsyncSession, feat_id: uuid.UUID) -> Feat | None:
    """Return a single feat by ID (untranslated), or None if not found."""
    stmt = (
        select(Feat).where(Feat.id == feat_id).options(selectinload(Feat.prerequisites))
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_feat_translated(
    session: AsyncSession, feat_id: uuid.UUID, *, locale: str = "en"
) -> FeatRead | None:
    """Return a feat by ID with every translatable field resolved for `locale`."""
    feat = await get_feat(session, feat_id)
    if feat is None:
        return None
    t = await get_translated(
        session, FeatI18n, FeatI18n.entity_id, entity_id=feat.id, locale=locale
    )
    return FeatRead(
        id=feat.id,
        index=feat.index,
        name=t.name if t else "",
        description=t.description if t else "",
        is_custom=feat.is_custom,
        prerequisites=[
            FeatPrerequisiteRead.model_validate(p) for p in feat.prerequisites
        ],
    )


async def list_feats_translated(
    session: AsyncSession,
    *,
    search: str | None = None,
    include_custom: bool = True,
    campaign_id: uuid.UUID | None = None,
    locale: str = "en",
) -> list[FeatSummary]:
    """Return feats with `name` resolved for `locale`, optionally name-filtered.

    Mirrors `list_races_translated`: feat counts are small enough that
    resolving translations per-row here is simpler than a fallback-aware SQL
    join.
    """
    feats = await list_feats(
        session, include_custom=include_custom, campaign_id=campaign_id
    )
    summaries = []
    for feat in feats:
        t = await get_translated(
            session, FeatI18n, FeatI18n.entity_id, entity_id=feat.id, locale=locale
        )
        summaries.append(
            FeatSummary(
                id=feat.id,
                index=feat.index,
                name=t.name if t else "",
                is_custom=feat.is_custom,
            )
        )
    if search:
        needle = search.lower()
        summaries = [s for s in summaries if needle in s.name.lower()]
    summaries.sort(key=lambda s: s.name)
    return summaries


# --- Monsters / stat blocks (SRD 2014 §7.4.8) -------------------------------

#: Eager-load options shared by `list_monsters`/`get_monster`.
_MONSTER_LOAD_OPTIONS = (
    selectinload(Monster.speed),
    selectinload(Monster.senses),
    selectinload(Monster.armor_classes),
    selectinload(Monster.proficiencies).selectinload(MonsterProficiency.proficiency),
    selectinload(Monster.damage_modifiers).selectinload(MonsterDamageModifier.damage_type),
    selectinload(Monster.condition_immunities).selectinload(
        MonsterConditionImmunity.condition
    ),
    selectinload(Monster.actions)
    .selectinload(MonsterAction.damages)
    .selectinload(MonsterActionDamage.damage_type),
    selectinload(Monster.legendary_actions)
    .selectinload(MonsterLegendaryAction.damages)
    .selectinload(MonsterLegendaryActionDamage.damage_type),
    selectinload(Monster.reactions)
    .selectinload(MonsterReaction.damages)
    .selectinload(MonsterReactionDamage.damage_type),
    selectinload(Monster.special_abilities)
    .selectinload(MonsterSpecialAbility.damages)
    .selectinload(MonsterSpecialAbilityDamage.damage_type),
)


async def list_monsters(
    session: AsyncSession,
    *,
    include_custom: bool = True,
    campaign_id: uuid.UUID | None = None,
) -> list[Monster]:
    """Return all monsters (base rows, eager-loaded stat block, untranslated).

    See `list_races` for the `campaign_id` vs. `include_custom` scoping rules.
    """
    stmt = select(Monster).options(*_MONSTER_LOAD_OPTIONS)
    if campaign_id is not None:
        stmt = stmt.where(
            or_(Monster.campaign_id.is_(None), Monster.campaign_id == campaign_id)
        )
    elif not include_custom:
        stmt = stmt.where(Monster.is_custom.is_(False))
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_monster(session: AsyncSession, monster_id: uuid.UUID) -> Monster | None:
    """Return a single monster by ID (untranslated), or None if not found."""
    stmt = (
        select(Monster).where(Monster.id == monster_id).options(*_MONSTER_LOAD_OPTIONS)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


def _to_monster_action_read(
    action: MonsterAction
    | MonsterLegendaryAction
    | MonsterReaction
    | MonsterSpecialAbility,
) -> MonsterActionRead:
    """Convert any of the four action-shaped models into the shared read schema.

    Unlike most catalog text, action `name`/`description` live directly on the
    row (PRD §7.4.8 has no `_i18n` sibling for these four tables) — no
    translation lookup needed here.
    """
    return MonsterActionRead(
        id=action.id,
        name=action.name,
        description=action.description,
        attack_bonus=action.attack_bonus,
        save_ability_score_id=action.save_ability_score_id,
        save_dc=action.save_dc,
        usage_type=action.usage_type,
        usage_times=action.usage_times,
        damages=[
            MonsterActionDamageRead(
                id=d.id,
                damage_dice=d.damage_dice,
                damage_type=d.damage_type.index or "",
            )
            for d in action.damages
        ],
    )


async def get_monster_translated(
    session: AsyncSession, monster_id: uuid.UUID, *, locale: str = "en"
) -> MonsterRead | None:
    """Return a monster by ID with every translatable field resolved for `locale`."""
    monster = await get_monster(session, monster_id)
    if monster is None:
        return None
    t = await get_translated(
        session, MonsterI18n, MonsterI18n.entity_id, entity_id=monster.id, locale=locale
    )
    return MonsterRead(
        id=monster.id,
        index=monster.index,
        name=t.name if t else "",
        description=t.description if t else "",
        size=monster.size,
        creature_type=monster.creature_type,
        creature_subtype=monster.creature_subtype,
        alignment=monster.alignment,
        hit_points=monster.hit_points,
        hit_dice=monster.hit_dice,
        challenge_rating=monster.challenge_rating,
        xp=monster.xp,
        proficiency_bonus=monster.proficiency_bonus,
        languages=monster.languages,
        strength=monster.strength,
        dexterity=monster.dexterity,
        constitution=monster.constitution,
        intelligence=monster.intelligence,
        wisdom=monster.wisdom,
        charisma=monster.charisma,
        is_custom=monster.is_custom,
        speed=MonsterSpeedRead.model_validate(monster.speed) if monster.speed else None,
        senses=(
            MonsterSenseRead.model_validate(monster.senses) if monster.senses else None
        ),
        armor_classes=[
            MonsterArmorClassRead.model_validate(ac) for ac in monster.armor_classes
        ],
        proficiencies=[
            MonsterProficiencyRead(
                id=p.id, proficiency_id=p.proficiency_id, value=p.value
            )
            for p in monster.proficiencies
        ],
        damage_modifiers=[
            MonsterDamageModifierRead(
                id=dm.id,
                damage_type=dm.damage_type.index or "",
                modifier_type=dm.modifier_type,
            )
            for dm in monster.damage_modifiers
        ],
        condition_immunities=[
            MonsterConditionImmunityRead(id=ci.id, condition=ci.condition.index or "")
            for ci in monster.condition_immunities
        ],
        actions=[_to_monster_action_read(a) for a in monster.actions],
        legendary_actions=[
            _to_monster_action_read(a) for a in monster.legendary_actions
        ],
        reactions=[_to_monster_action_read(a) for a in monster.reactions],
        special_abilities=[
            _to_monster_action_read(a) for a in monster.special_abilities
        ],
    )


async def list_monsters_translated(
    session: AsyncSession,
    *,
    search: str | None = None,
    include_custom: bool = True,
    campaign_id: uuid.UUID | None = None,
    locale: str = "en",
) -> list[MonsterSummary]:
    """Return monsters with `name` resolved for `locale`, optionally name-filtered.

    Mirrors `list_races_translated`: monster counts are small enough (this
    story's seed) that resolving translations per-row here is simpler than a
    fallback-aware SQL join.
    """
    monsters = await list_monsters(
        session, include_custom=include_custom, campaign_id=campaign_id
    )
    summaries = []
    for monster in monsters:
        t = await get_translated(
            session,
            MonsterI18n,
            MonsterI18n.entity_id,
            entity_id=monster.id,
            locale=locale,
        )
        summaries.append(
            MonsterSummary(
                id=monster.id,
                index=monster.index,
                name=t.name if t else "",
                size=monster.size,
                creature_type=monster.creature_type,
                challenge_rating=monster.challenge_rating,
                is_custom=monster.is_custom,
            )
        )
    if search:
        needle = search.lower()
        summaries = [s for s in summaries if needle in s.name.lower()]
    summaries.sort(key=lambda s: s.name)
    return summaries


# --- Rules narrativas (SRD 2014 §7.4.9) --------------------------------------


async def list_rule_sections(session: AsyncSession) -> list[RuleSection]:
    """Return all rule sections."""
    result = await session.execute(
        select(RuleSection).order_by(RuleSection.index)
    )
    return list(result.scalars().all())


async def _translate_rule_section(
    session: AsyncSession, section: RuleSection, locale: str
) -> RuleSectionRead:
    t = await get_translated(
        session,
        RuleSectionI18n,
        RuleSectionI18n.entity_id,
        entity_id=section.id,
        locale=locale,
    )
    return RuleSectionRead(
        id=section.id,
        index=section.index,
        name=t.name if t else "",
        desc=t.desc if t else "",
        is_custom=section.is_custom,
    )


async def list_rules(session: AsyncSession) -> list[Rule]:
    """Return all rules (base rows, eager-loaded sections, untranslated)."""
    stmt = select(Rule).options(
        selectinload(Rule.sections).selectinload(RuleRuleSection.rule_section)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_rule(session: AsyncSession, rule_id: uuid.UUID) -> Rule | None:
    """Return a single rule by ID (untranslated), or None if not found."""
    stmt = (
        select(Rule)
        .where(Rule.id == rule_id)
        .options(selectinload(Rule.sections).selectinload(RuleRuleSection.rule_section))
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_rule_translated(
    session: AsyncSession, rule_id: uuid.UUID, *, locale: str = "en"
) -> RuleRead | None:
    """Return a rule by ID with every translatable field resolved for `locale`."""
    rule = await get_rule(session, rule_id)
    if rule is None:
        return None
    t = await get_translated(
        session, RuleI18n, RuleI18n.entity_id, entity_id=rule.id, locale=locale
    )
    sections = [
        await _translate_rule_section(session, rrs.rule_section, locale)
        for rrs in rule.sections
    ]
    return RuleRead(
        id=rule.id,
        index=rule.index,
        name=t.name if t else "",
        desc=t.desc if t else "",
        is_custom=rule.is_custom,
        sections=sections,
    )


async def list_rules_translated(
    session: AsyncSession, *, search: str | None = None, locale: str = "en"
) -> list[RuleSummary]:
    """Return rules with `name` resolved for `locale`, optionally name-filtered."""
    rules = await list_rules(session)
    summaries = []
    for rule in rules:
        t = await get_translated(
            session, RuleI18n, RuleI18n.entity_id, entity_id=rule.id, locale=locale
        )
        summaries.append(
            RuleSummary(
                id=rule.id,
                index=rule.index,
                name=t.name if t else "",
                is_custom=rule.is_custom,
            )
        )
    if search:
        needle = search.lower()
        summaries = [s for s in summaries if needle in s.name.lower()]
    summaries.sort(key=lambda s: s.name)
    return summaries


# --- Homebrew creation (v1: races, classes, spells, items, monsters) ---------
#
# Always scoped to a campaign (`is_custom=True` + `campaign_id`, PRD §7.4) —
# caller (router) is responsible for verifying the requester is the DM of
# `data.campaign_id` before calling any of these.

_ITEM_TYPE_TO_EQUIPMENT_CATEGORY_INDEX = {
    "weapon": "weapon",
    "armor": "armor",
    "gear": "adventuring-gear",
    "tool": "tools",
    "consumable": "adventuring-gear",
}


async def create_custom_race(session: AsyncSession, data: RaceCreate) -> RaceRead:
    """Create a homebrew race and return it translated (locale `en`)."""
    validate_custom_campaign_scope(is_custom=True, campaign_id=data.campaign_id)
    race = Race(
        speed=data.speed,
        size=data.size,
        darkvision_range=data.darkvision_range,
        is_custom=True,
        campaign_id=data.campaign_id,
    )
    session.add(race)
    await session.flush()
    session.add(
        RaceI18n(
            entity_id=race.id,
            locale="en",
            name=data.name,
            description=data.description,
        )
    )
    await session.commit()
    result = await get_race_translated(session, race.id, locale="en")
    assert result is not None  # just created it
    return result


async def create_custom_class(
    session: AsyncSession, data: ClassDefinitionCreate
) -> ClassDefinitionRead:
    """Create a homebrew class and return it translated (locale `en`)."""
    validate_custom_campaign_scope(is_custom=True, campaign_id=data.campaign_id)
    class_definition = ClassDefinition(
        hit_die=data.hit_die,
        primary_ability=data.primary_ability,
        saving_throw_proficiencies=data.saving_throw_proficiencies,
        is_custom=True,
        campaign_id=data.campaign_id,
    )
    session.add(class_definition)
    await session.flush()
    session.add(
        ClassDefinitionI18n(entity_id=class_definition.id, locale="en", name=data.name)
    )
    await session.commit()
    result = await get_class_translated(session, class_definition.id, locale="en")
    assert result is not None  # just created it
    return result


async def create_custom_spell(session: AsyncSession, data: SpellCreate) -> SpellRead:
    """Create a homebrew spell and return it translated (locale `en`).

    Raises 422 if `data.school` doesn't match a seeded `MagicSchool.index`.
    """
    validate_custom_campaign_scope(is_custom=True, campaign_id=data.campaign_id)
    school_result = await session.execute(
        select(MagicSchool).where(MagicSchool.index == data.school)
    )
    magic_school = school_result.scalar_one_or_none()
    if magic_school is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Unknown magic school '{data.school}'",
        )

    spell = Spell(
        level=data.level,
        magic_school_id=magic_school.id,
        casting_time=data.casting_time,
        range=data.range,
        duration=data.duration,
        components=data.components,
        ritual=data.ritual,
        concentration=data.concentration,
        is_custom=True,
        campaign_id=data.campaign_id,
    )
    session.add(spell)
    await session.flush()
    session.add(
        SpellI18n(
            entity_id=spell.id,
            locale="en",
            name=data.name,
            description=data.description,
            higher_levels=data.higher_levels,
        )
    )
    await session.commit()
    result = await get_spell_translated(session, spell.id, locale="en")
    assert result is not None  # just created it
    return result


async def create_custom_item(session: AsyncSession, data: ItemCreate) -> ItemRead:
    """Create a homebrew item and return it translated (locale `en`).

    The equipment category is derived from `item_type` (v1 simplification —
    homebrew items reuse an existing SRD category rather than picking a
    fine-grained one). Raises 422 if that category isn't seeded.
    """
    validate_custom_campaign_scope(is_custom=True, campaign_id=data.campaign_id)
    category_index = _ITEM_TYPE_TO_EQUIPMENT_CATEGORY_INDEX[data.item_type.value]
    category_result = await session.execute(
        select(EquipmentCategory).where(EquipmentCategory.index == category_index)
    )
    equipment_category = category_result.scalar_one_or_none()
    if equipment_category is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Catalog isn't seeded with equipment categories yet",
        )

    item = Item(
        item_type=data.item_type,
        equipment_category_id=equipment_category.id,
        rarity=data.rarity,
        weight=data.weight,
        cost=data.cost,
        is_custom=True,
        campaign_id=data.campaign_id,
    )
    session.add(item)
    await session.flush()
    session.add(
        ItemI18n(
            entity_id=item.id,
            locale="en",
            name=data.name,
            description=data.description,
        )
    )
    await session.commit()
    result = await get_item_translated(session, item.id, locale="en")
    assert result is not None  # just created it
    return result


async def create_custom_monster(
    session: AsyncSession, data: MonsterCreate
) -> MonsterRead:
    """Create a homebrew monster and return it translated (locale `en`)."""
    validate_custom_campaign_scope(is_custom=True, campaign_id=data.campaign_id)
    monster = Monster(
        size=data.size,
        creature_type=data.creature_type,
        alignment=data.alignment,
        hit_points=data.hit_points,
        hit_dice=data.hit_dice,
        challenge_rating=data.challenge_rating,
        xp=data.xp,
        languages=data.languages,
        strength=data.strength,
        dexterity=data.dexterity,
        constitution=data.constitution,
        intelligence=data.intelligence,
        wisdom=data.wisdom,
        charisma=data.charisma,
        is_custom=True,
        campaign_id=data.campaign_id,
    )
    session.add(monster)
    await session.flush()
    session.add(
        MonsterI18n(
            entity_id=monster.id,
            locale="en",
            name=data.name,
            description=data.description,
        )
    )
    await session.commit()
    result = await get_monster_translated(session, monster.id, locale="en")
    assert result is not None  # just created it
    return result
