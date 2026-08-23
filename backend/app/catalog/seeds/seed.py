"""Seed function to populate catalog tables from SRD JSON data."""

import json
import uuid
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.catalog.models import (
    ArmorDetail,
    ClassDefinition,
    ClassDefinitionI18n,
    ClassLevel,
    ClassLevelFeature,
    ClassLevelResource,
    ClassLevelSpellSlot,
    DamageType,
    DamageTypeI18n,
    EquipmentCategory,
    EquipmentCategoryI18n,
    Feature,
    FeatureI18n,
    FeaturePrerequisite,
    Item,
    ItemI18n,
    ItemProperty,
    MagicItem,
    MagicItemI18n,
    MagicSchool,
    MagicSchoolI18n,
    Race,
    RaceAbilityBonus,
    RaceI18n,
    RaceTrait,
    RaceTraitI18n,
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

#: Fixed vocabulary (PRD §7.4.1) has no seed of its own yet (a later backlog
#: story covers all 24 categories from `_data/2014`), but several catalogs
#: added in later stories reference it via FK. `_ensure_fixed_vocab` below
#: seeds just what each story's data actually references, idempotently by
#: `index` — these dicts are the `index` -> English display name for each.
_MAGIC_SCHOOL_NAMES = {
    "abjuration": "Abjuration",
    "conjuration": "Conjuration",
    "divination": "Divination",
    "enchantment": "Enchantment",
    "evocation": "Evocation",
    "illusion": "Illusion",
    "necromancy": "Necromancy",
    "transmutation": "Transmutation",
}
_WEAPON_PROPERTY_NAMES = {
    "versatile": "Versatile",
    "finesse": "Finesse",
    "light": "Light",
    "thrown": "Thrown",
    "heavy": "Heavy",
    "two-handed": "Two-Handed",
    "ammunition": "Ammunition",
}
_DAMAGE_TYPE_NAMES = {
    "slashing": "Slashing",
    "piercing": "Piercing",
    "bludgeoning": "Bludgeoning",
}
_EQUIPMENT_CATEGORY_NAMES = {
    "simple-weapons": "Simple Weapons",
    "martial-weapons": "Martial Weapons",
    "light-armor": "Light Armor",
    "medium-armor": "Medium Armor",
    "heavy-armor": "Heavy Armor",
    "shields": "Shields",
    "adventuring-gear": "Adventuring Gear",
}


async def _ensure_fixed_vocab(
    session: AsyncSession,
    model: Any,
    i18n_model: Any,
    names: dict[str, str],
) -> dict[str, uuid.UUID]:
    """Get-or-create fixed-vocabulary rows by `index`, returning `index` -> id.

    Shared by every later-story seed that needs a §7.4.1 category as an FK
    target (magic schools, weapon properties, damage types, equipment
    categories) before that category has its own seed story.
    """
    result = await session.execute(select(model))
    by_index = {row.index: row.id for row in result.scalars().all() if row.index}
    for index, name in names.items():
        if index in by_index:
            continue
        row = model(id=uuid.uuid4(), index=index, is_custom=False)
        session.add(row)
        await _seed_i18n(session, i18n_model, row.id, {"en": {"name": name}})
        by_index[index] = row.id
    return by_index

_DATA_DIR = Path(__file__).parent / "data"


async def _seed_i18n(
    session: AsyncSession,
    # Typed loosely: every `_i18n` model shares id/entity_id/locale plus its
    # own translated columns (see `app.catalog.mixins.CatalogI18nMixin`), but
    # that mixin alone doesn't expose enough for mypy to check the **fields
    # kwargs against each concrete subclass's constructor.
    i18n_model: Any,
    entity_id: uuid.UUID,
    translations: dict[str, dict[str, str | None]],
) -> None:
    """Add one `_i18n` row per locale in `translations` (e.g. `{"en": {...}}`).

    Flushes first so `entity_id`'s parent row exists before the FK-backed
    `_i18n` insert — dialects that enforce FKs at insert time (Postgres, unlike
    SQLite's default) reject an out-of-order autoflush otherwise, since the
    parent and `_i18n` row are usually `add()`-ed in separate statements.
    """
    await session.flush()
    for locale, fields in translations.items():
        session.add(
            i18n_model(id=uuid.uuid4(), entity_id=entity_id, locale=locale, **fields)
        )


async def seed_catalog(session: AsyncSession) -> None:
    """Populate catalog tables from JSON files if they are empty."""
    await _seed_races(session)
    await _seed_classes(session)
    await _seed_spells(session)
    await _seed_items(session)
    await _seed_magic_items(session)
    await session.commit()


async def _seed_races(session: AsyncSession) -> None:
    count = await session.scalar(select(Race).limit(1))
    if count is not None:
        return

    data = json.loads((_DATA_DIR / "races.json").read_text())
    for entry in data:
        race = Race(
            id=uuid.uuid4(),
            index=entry["index"],
            speed=entry["speed"],
            size=entry["size"],
            darkvision_range=entry["darkvision_range"],
            is_custom=False,
        )
        session.add(race)
        await _seed_i18n(session, RaceI18n, race.id, entry["i18n"])

        for ab in entry.get("ability_bonuses", []):
            session.add(
                RaceAbilityBonus(
                    id=uuid.uuid4(),
                    race_id=race.id,
                    ability=ab["ability"],
                    bonus=ab["bonus"],
                )
            )

        for t in entry.get("traits", []):
            trait = RaceTrait(
                id=uuid.uuid4(),
                race_id=race.id,
                mechanical_effect=t.get("mechanical_effect"),
            )
            session.add(trait)
            await _seed_i18n(session, RaceTraitI18n, trait.id, t["i18n"])

        for sr_data in entry.get("subraces", []):
            subrace = Subrace(
                id=uuid.uuid4(),
                race_id=race.id,
                index=sr_data["index"],
            )
            session.add(subrace)
            await _seed_i18n(session, SubraceI18n, subrace.id, sr_data["i18n"])

            for ab in sr_data.get("ability_bonuses", []):
                session.add(
                    RaceAbilityBonus(
                        id=uuid.uuid4(),
                        subrace_id=subrace.id,
                        ability=ab["ability"],
                        bonus=ab["bonus"],
                    )
                )

            for t in sr_data.get("traits", []):
                subrace_trait = SubraceTrait(
                    id=uuid.uuid4(),
                    subrace_id=subrace.id,
                    mechanical_effect=t.get("mechanical_effect"),
                )
                session.add(subrace_trait)
                await _seed_i18n(session, SubraceTraitI18n, subrace_trait.id, t["i18n"])


async def _seed_class_feature(
    session: AsyncSession,
    feat: dict[str, Any],
    *,
    owning_class_definition_id: uuid.UUID,
    feature_class_definition_id: uuid.UUID | None,
    feature_subclass_definition_id: uuid.UUID | None,
    class_level_by_level: dict[int, ClassLevel],
) -> Feature:
    """Create a Feature row and attach it to the matching ClassLevel via the junction.

    `owning_class_definition_id` is always the parent ClassDefinition (required
    on every `ClassLevel` row, even a subclass-specific one); the two
    `feature_*_definition_id` params set `Feature`'s own mutually-exclusive
    owner FKs.
    """
    feature = Feature(
        id=uuid.uuid4(),
        index=feat["index"],
        class_definition_id=feature_class_definition_id,
        subclass_definition_id=feature_subclass_definition_id,
        level=feat["level"],
        mechanical_effect=feat.get("mechanical_effect"),
        is_custom=False,
    )
    session.add(feature)
    await _seed_i18n(session, FeatureI18n, feature.id, feat["i18n"])

    class_level = class_level_by_level.get(feat["level"])
    if class_level is None:
        # Subclass feature at a level with no ClassLevel row yet — create the
        # subclass-specific progression row on demand (see PRD §7.4.4:
        # `ClassLevel.subclass_definition_id` tracks a subclass's own grants).
        class_level = ClassLevel(
            id=uuid.uuid4(),
            class_definition_id=owning_class_definition_id,
            subclass_definition_id=feature_subclass_definition_id,
            level=feat["level"],
        )
        session.add(class_level)
        class_level_by_level[feat["level"]] = class_level
    session.add(
        ClassLevelFeature(
            id=uuid.uuid4(), class_level_id=class_level.id, feature_id=feature.id
        )
    )
    return feature


async def _seed_classes(session: AsyncSession) -> None:
    count = await session.scalar(select(ClassDefinition).limit(1))
    if count is not None:
        return

    data = json.loads((_DATA_DIR / "classes.json").read_text())
    for entry in data:
        cls = ClassDefinition(
            id=uuid.uuid4(),
            index=entry["index"],
            hit_die=entry["hit_die"],
            primary_ability=entry["primary_ability"],
            saving_throw_proficiencies=entry["saving_throw_proficiencies"],
            is_custom=False,
        )
        session.add(cls)
        await _seed_i18n(session, ClassDefinitionI18n, cls.id, entry["i18n"])

        base_levels: dict[int, ClassLevel] = {}
        for lvl in entry["class_levels"]:
            class_level = ClassLevel(
                id=uuid.uuid4(),
                class_definition_id=cls.id,
                subclass_definition_id=None,
                level=lvl["level"],
                proficiency_bonus=lvl["proficiency_bonus"],
                ability_score_bonuses=lvl["ability_score_bonuses"],
            )
            session.add(class_level)
            base_levels[lvl["level"]] = class_level

            for slot in lvl.get("spell_slots", []):
                session.add(
                    ClassLevelSpellSlot(
                        id=uuid.uuid4(),
                        class_level_id=class_level.id,
                        spell_level=slot["spell_level"],
                        slot_count=slot["slot_count"],
                    )
                )
            for res in lvl.get("resources", []):
                session.add(
                    ClassLevelResource(
                        id=uuid.uuid4(),
                        class_level_id=class_level.id,
                        resource_key=res["resource_key"],
                        value=res["value"],
                    )
                )

        features_by_index: dict[str, Feature] = {}
        pending_prerequisites: list[tuple[Feature, dict[str, Any]]] = []
        for feat in entry.get("features", []):
            feature = await _seed_class_feature(
                session,
                feat,
                owning_class_definition_id=cls.id,
                feature_class_definition_id=cls.id,
                feature_subclass_definition_id=None,
                class_level_by_level=base_levels,
            )
            features_by_index[feat["index"]] = feature
            for prereq in feat.get("prerequisites", []):
                pending_prerequisites.append((feature, prereq))

        for feature, prereq in pending_prerequisites:
            required = features_by_index.get(prereq.get("required_feature_index", ""))
            session.add(
                FeaturePrerequisite(
                    id=uuid.uuid4(),
                    feature_id=feature.id,
                    prerequisite_type=prereq["prerequisite_type"],
                    level=prereq.get("level"),
                    required_feature_id=required.id if required else None,
                    spell_id=None,
                )
            )

        for sc in entry.get("subclasses", []):
            subclass = SubclassDefinition(
                id=uuid.uuid4(),
                class_definition_id=cls.id,
                index=sc["index"],
                is_custom=False,
            )
            session.add(subclass)
            await _seed_i18n(session, SubclassDefinitionI18n, subclass.id, sc["i18n"])

            subclass_levels: dict[int, ClassLevel] = {}
            for feat in sc.get("features", []):
                await _seed_class_feature(
                    session,
                    feat,
                    owning_class_definition_id=cls.id,
                    feature_class_definition_id=None,
                    feature_subclass_definition_id=subclass.id,
                    class_level_by_level=subclass_levels,
                )


async def _seed_spells(session: AsyncSession) -> None:
    count = await session.scalar(select(Spell).limit(1))
    if count is not None:
        return

    schools_by_index = await _ensure_fixed_vocab(
        session, MagicSchool, MagicSchoolI18n, _MAGIC_SCHOOL_NAMES
    )
    classes_result = await session.execute(select(ClassDefinition))
    classes_by_index = {
        c.index: c.id for c in classes_result.scalars().all() if c.index
    }

    data = json.loads((_DATA_DIR / "spells.json").read_text())
    for entry in data:
        spell = Spell(
            id=uuid.uuid4(),
            index=entry["index"],
            level=entry["level"],
            magic_school_id=schools_by_index[entry["magic_school_index"]],
            casting_time=entry["casting_time"],
            range=entry["range"],
            duration=entry["duration"],
            components=entry["components"],
            ritual=entry["ritual"],
            concentration=entry["concentration"],
            is_custom=False,
        )
        session.add(spell)
        await _seed_i18n(session, SpellI18n, spell.id, entry["i18n"])

        for class_index in entry.get("classes", []):
            class_id = classes_by_index.get(class_index)
            if class_id is not None:
                session.add(
                    SpellClass(
                        id=uuid.uuid4(),
                        spell_id=spell.id,
                        class_definition_id=class_id,
                    )
                )


async def _seed_items(session: AsyncSession) -> None:
    count = await session.scalar(select(Item).limit(1))
    if count is not None:
        return

    categories_by_index = await _ensure_fixed_vocab(
        session, EquipmentCategory, EquipmentCategoryI18n, _EQUIPMENT_CATEGORY_NAMES
    )
    properties_by_index = await _ensure_fixed_vocab(
        session, WeaponProperty, WeaponPropertyI18n, _WEAPON_PROPERTY_NAMES
    )
    damage_types_by_index = await _ensure_fixed_vocab(
        session, DamageType, DamageTypeI18n, _DAMAGE_TYPE_NAMES
    )

    data = json.loads((_DATA_DIR / "items.json").read_text())
    for entry in data:
        item = Item(
            id=uuid.uuid4(),
            index=entry["index"],
            item_type=entry["item_type"],
            equipment_category_id=categories_by_index[entry["equipment_category_index"]],
            rarity=entry.get("rarity"),
            weight=entry["weight"],
            cost=entry["cost"],
            is_custom=False,
        )
        session.add(item)
        await _seed_i18n(session, ItemI18n, item.id, entry["i18n"])

        for prop_index in entry.get("properties", []):
            property_id = properties_by_index.get(prop_index)
            if property_id is not None:
                session.add(
                    ItemProperty(
                        id=uuid.uuid4(), item_id=item.id, weapon_property_id=property_id
                    )
                )

        if wd := entry.get("weapon_detail"):
            session.add(
                WeaponDetail(
                    id=uuid.uuid4(),
                    item_id=item.id,
                    damage_dice=wd["damage_dice"],
                    damage_type_id=damage_types_by_index[wd["damage_type_index"]],
                    weapon_range=wd["weapon_range"],
                )
            )

        if ad := entry.get("armor_detail"):
            session.add(
                ArmorDetail(
                    id=uuid.uuid4(),
                    item_id=item.id,
                    base_ac=ad["base_ac"],
                    dex_bonus_cap=ad.get("dex_bonus_cap"),
                    stealth_disadvantage=ad["stealth_disadvantage"],
                    strength_requirement=ad.get("strength_requirement"),
                )
            )

async def _seed_magic_item_entry(
    session: AsyncSession,
    entry: dict[str, Any],
    *,
    equipment_category_id: uuid.UUID,
    variant_of_id: uuid.UUID | None,
) -> None:
    """Create one MagicItem row (+ i18n) and recurse into its `variants`, if any.

    A variant (e.g. a +2 version) shares its base item's equipment category —
    `variants.json` entries don't repeat `equipment_category_index`, so the
    resolved id is threaded down through the recursion instead.
    """
    magic_item = MagicItem(
        id=uuid.uuid4(),
        index=entry["index"],
        equipment_category_id=equipment_category_id,
        rarity=entry["rarity"],
        is_custom=False,
        is_variant=variant_of_id is not None,
        variant_of_id=variant_of_id,
    )
    session.add(magic_item)
    await _seed_i18n(session, MagicItemI18n, magic_item.id, entry["i18n"])

    for variant in entry.get("variants", []):
        await _seed_magic_item_entry(
            session,
            variant,
            equipment_category_id=equipment_category_id,
            variant_of_id=magic_item.id,
        )


async def _seed_magic_items(session: AsyncSession) -> None:
    count = await session.scalar(select(MagicItem).limit(1))
    if count is not None:
        return

    categories_by_index = await _ensure_fixed_vocab(
        session, EquipmentCategory, EquipmentCategoryI18n, _EQUIPMENT_CATEGORY_NAMES
    )

    data = json.loads((_DATA_DIR / "magic_items.json").read_text())
    for entry in data:
        await _seed_magic_item_entry(
            session,
            entry,
            equipment_category_id=categories_by_index[entry["equipment_category_index"]],
            variant_of_id=None,
        )
