"""Seed function to populate catalog tables from SRD JSON data.

Data files under `data/` are the normalized output of `convert_srd.py` (run
once against `_data/2014/en/*.json` and committed) — see that module's
docstring for why conversion is a pre-generation step rather than something
`seed_catalog` does at runtime.
"""

import json
import uuid
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.catalog.models import (
    AbilityScoreDefinition,
    AbilityScoreDefinitionI18n,
    Alignment,
    AlignmentI18n,
    ArmorDetail,
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
    ClassLevelResource,
    ClassLevelSpellSlot,
    Condition,
    ConditionI18n,
    DamageType,
    DamageTypeI18n,
    EquipmentCategory,
    EquipmentCategoryI18n,
    Feat,
    FeatI18n,
    FeatPrerequisite,
    Feature,
    FeatureI18n,
    FeaturePrerequisite,
    Item,
    ItemI18n,
    ItemProperty,
    Language,
    LanguageI18n,
    MagicItem,
    MagicItemI18n,
    MagicSchool,
    MagicSchoolI18n,
    Monster,
    MonsterAction,
    MonsterActionDamage,
    MonsterArmorClass,
    MonsterConditionImmunity,
    MonsterDamageModifier,
    MonsterI18n,
    MonsterLegendaryAction,
    MonsterLegendaryActionDamage,
    MonsterProficiency,
    MonsterReaction,
    MonsterReactionDamage,
    MonsterSense,
    MonsterSpecialAbility,
    MonsterSpecialAbilityDamage,
    MonsterSpeed,
    Proficiency,
    ProficiencyClass,
    ProficiencyI18n,
    ProficiencyRace,
    Race,
    RaceAbilityBonus,
    RaceI18n,
    RaceTrait,
    RaceTraitI18n,
    Rule,
    RuleI18n,
    RuleRuleSection,
    RuleSection,
    RuleSectionI18n,
    SkillDefinition,
    SkillDefinitionI18n,
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

_DATA_DIR = Path(__file__).parent / "data"


def _load(name: str) -> Any:
    return json.loads((_DATA_DIR / f"{name}.json").read_text())


def _load_pt_br(name: str) -> dict[str, dict[str, str | None]]:
    """`index` -> translated fields for `name`, or `{}` if no pt-BR file exists.

    Only 12 of the 24 categories have one (see `convert_srd`'s pt-BR section
    for which, and why some nested text is left out even there) — the rest
    simply have no `{name}_pt_br.json`, and every entity in them keeps
    resolving to `en` via `get_translated`'s locale fallback.
    """
    path = _DATA_DIR / f"{name}_pt_br.json"
    return json.loads(path.read_text()) if path.exists() else {}


def _translations(
    en_fields: dict[str, str | None],
    pt_br_by_index: dict[str, dict[str, str | None]],
    index: str,
) -> dict[str, dict[str, str | None]]:
    """Build a `_seed_i18n` translations dict: `en` always, `pt-BR` when available."""
    translations = {"en": en_fields}
    pt_br = pt_br_by_index.get(index)
    if pt_br:
        translations["pt-BR"] = pt_br
    return translations


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


async def _index_map(session: AsyncSession, model: Any) -> dict[str, uuid.UUID]:
    """`index` -> `id` for every row of `model` that has one set."""
    result = await session.execute(select(model))
    return {row.index: row.id for row in result.scalars().all() if row.index}


async def seed_catalog(session: AsyncSession) -> None:
    """Populate catalog tables from JSON files if they are empty."""
    await _seed_ability_scores(session)
    await _seed_skills(session)
    await _seed_alignments(session)
    await _seed_conditions(session)
    await _seed_damage_types(session)
    await _seed_magic_schools(session)
    await _seed_languages(session)
    await _seed_weapon_properties(session)
    await _seed_equipment_categories(session)
    await _seed_proficiencies(session)
    await _seed_races(session)
    await _seed_classes(session)
    await _seed_spells(session)
    await _seed_items(session)
    await _seed_magic_items(session)
    await _seed_backgrounds(session)
    await _seed_feats(session)
    await _seed_monsters(session)
    await _seed_rules(session)
    await session.commit()


# --- Fixed vocabulary (PRD §7.4.1) ------------------------------------------


async def _seed_ability_scores(session: AsyncSession) -> None:
    if await session.scalar(select(AbilityScoreDefinition).limit(1)) is not None:
        return
    pt_br_by_index = _load_pt_br("ability_scores")
    for entry in _load("ability_scores"):
        row = AbilityScoreDefinition(
            id=uuid.uuid4(), index=entry["index"], is_custom=False
        )
        session.add(row)
        await _seed_i18n(
            session,
            AbilityScoreDefinitionI18n,
            row.id,
            _translations(
                {
                    "name": entry["name"],
                    "full_name": entry["full_name"],
                    "desc": entry["desc"],
                },
                pt_br_by_index,
                entry["index"],
            ),
        )


async def _seed_skills(session: AsyncSession) -> None:
    if await session.scalar(select(SkillDefinition).limit(1)) is not None:
        return
    ability_scores_by_index = await _index_map(session, AbilityScoreDefinition)
    pt_br_by_index = _load_pt_br("skills")
    for entry in _load("skills"):
        row = SkillDefinition(
            id=uuid.uuid4(),
            index=entry["index"],
            ability_score_id=ability_scores_by_index[entry["ability_score_index"]],
            is_custom=False,
        )
        session.add(row)
        await _seed_i18n(
            session,
            SkillDefinitionI18n,
            row.id,
            _translations(
                {"name": entry["name"], "desc": entry["desc"]},
                pt_br_by_index,
                entry["index"],
            ),
        )


async def _seed_alignments(session: AsyncSession) -> None:
    if await session.scalar(select(Alignment).limit(1)) is not None:
        return
    pt_br_by_index = _load_pt_br("alignments")
    for entry in _load("alignments"):
        row = Alignment(id=uuid.uuid4(), index=entry["index"], is_custom=False)
        session.add(row)
        await _seed_i18n(
            session,
            AlignmentI18n,
            row.id,
            _translations(
                {
                    "name": entry["name"],
                    "abbreviation": entry["abbreviation"],
                    "desc": entry["desc"],
                },
                pt_br_by_index,
                entry["index"],
            ),
        )


async def _seed_conditions(session: AsyncSession) -> None:
    if await session.scalar(select(Condition).limit(1)) is not None:
        return
    pt_br_by_index = _load_pt_br("conditions")
    for entry in _load("conditions"):
        row = Condition(id=uuid.uuid4(), index=entry["index"], is_custom=False)
        session.add(row)
        await _seed_i18n(
            session,
            ConditionI18n,
            row.id,
            _translations(
                {"name": entry["name"], "desc": entry["desc"]},
                pt_br_by_index,
                entry["index"],
            ),
        )


async def _seed_damage_types(session: AsyncSession) -> None:
    if await session.scalar(select(DamageType).limit(1)) is not None:
        return
    pt_br_by_index = _load_pt_br("damage_types")
    for entry in _load("damage_types"):
        row = DamageType(id=uuid.uuid4(), index=entry["index"], is_custom=False)
        session.add(row)
        await _seed_i18n(
            session,
            DamageTypeI18n,
            row.id,
            _translations(
                {"name": entry["name"], "desc": entry["desc"]},
                pt_br_by_index,
                entry["index"],
            ),
        )


async def _seed_magic_schools(session: AsyncSession) -> None:
    if await session.scalar(select(MagicSchool).limit(1)) is not None:
        return
    pt_br_by_index = _load_pt_br("magic_schools")
    for entry in _load("magic_schools"):
        row = MagicSchool(id=uuid.uuid4(), index=entry["index"], is_custom=False)
        session.add(row)
        await _seed_i18n(
            session,
            MagicSchoolI18n,
            row.id,
            _translations(
                {"name": entry["name"], "desc": entry["desc"]},
                pt_br_by_index,
                entry["index"],
            ),
        )


async def _seed_languages(session: AsyncSession) -> None:
    if await session.scalar(select(Language).limit(1)) is not None:
        return
    pt_br_by_index = _load_pt_br("languages")
    for entry in _load("languages"):
        row = Language(
            id=uuid.uuid4(),
            index=entry["index"],
            language_type=entry["language_type"],
            is_custom=False,
        )
        session.add(row)
        await _seed_i18n(
            session,
            LanguageI18n,
            row.id,
            _translations(
                {
                    "name": entry["name"],
                    "desc": entry["desc"],
                    "script": entry.get("script"),
                    "typical_speakers": entry.get("typical_speakers"),
                },
                pt_br_by_index,
                entry["index"],
            ),
        )


async def _seed_weapon_properties(session: AsyncSession) -> None:
    if await session.scalar(select(WeaponProperty).limit(1)) is not None:
        return
    pt_br_by_index = _load_pt_br("weapon_properties")
    for entry in _load("weapon_properties"):
        row = WeaponProperty(id=uuid.uuid4(), index=entry["index"], is_custom=False)
        session.add(row)
        await _seed_i18n(
            session,
            WeaponPropertyI18n,
            row.id,
            _translations(
                {"name": entry["name"], "desc": entry["desc"]},
                pt_br_by_index,
                entry["index"],
            ),
        )


async def _seed_equipment_categories(session: AsyncSession) -> None:
    if await session.scalar(select(EquipmentCategory).limit(1)) is not None:
        return
    for entry in _load("equipment_categories"):
        row = EquipmentCategory(id=uuid.uuid4(), index=entry["index"], is_custom=False)
        session.add(row)
        await _seed_i18n(
            session, EquipmentCategoryI18n, row.id, {"en": {"name": entry["name"]}}
        )


async def _seed_proficiencies(session: AsyncSession) -> None:
    """Seed Proficiency rows.

    ProficiencyClass/ProficiencyRace junctions wait for `_seed_classes`/
    `_seed_races` (they need ClassDefinition/Race ids).
    """
    if await session.scalar(select(Proficiency).limit(1)) is not None:
        return
    skills_by_index = await _index_map(session, SkillDefinition)
    ability_scores_by_index = await _index_map(session, AbilityScoreDefinition)
    categories_by_index = await _index_map(session, EquipmentCategory)
    for entry in _load("proficiencies"):
        row = Proficiency(
            id=uuid.uuid4(),
            index=entry["index"],
            proficiency_type=entry["proficiency_type"],
            skill_id=(
                skills_by_index[entry["skill_index"]] if entry["skill_index"] else None
            ),
            ability_score_id=(
                ability_scores_by_index[entry["ability_score_index"]]
                if entry["ability_score_index"]
                else None
            ),
            equipment_category_id=(
                categories_by_index[entry["equipment_category_index"]]
                if entry["equipment_category_index"]
                else None
            ),
            is_custom=False,
        )
        session.add(row)
        await _seed_i18n(
            session, ProficiencyI18n, row.id, {"en": {"name": entry["name"]}}
        )


async def _seed_proficiency_grants(
    session: AsyncSession,
    proficiencies_by_index: dict[str, uuid.UUID],
) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    """Class/race index -> list of Proficiency indexes granted by default.

    Read once from `proficiencies.json` (each entry lists the classes/races
    that grant it) and inverted here, since `_seed_races`/`_seed_classes`
    iterate per-race/per-class.
    """
    class_indexes: dict[str, list[str]] = {}
    race_indexes: dict[str, list[str]] = {}
    for entry in _load("proficiencies"):
        if entry["index"] not in proficiencies_by_index:
            continue
        for class_index in entry["class_indexes"]:
            class_indexes.setdefault(class_index, []).append(entry["index"])
        for race_index in entry["race_indexes"]:
            race_indexes.setdefault(race_index, []).append(entry["index"])
    return class_indexes, race_indexes


# --- Races (PRD §7.4.2) -----------------------------------------------------


async def _seed_races(session: AsyncSession) -> None:
    if await session.scalar(select(Race).limit(1)) is not None:
        return

    proficiencies_by_index = await _index_map(session, Proficiency)
    _, race_grants = await _seed_proficiency_grants(session, proficiencies_by_index)
    pt_br_by_index = _load_pt_br("races")

    data = _load("races")
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
        await _seed_i18n(
            session,
            RaceI18n,
            race.id,
            _translations(entry["i18n"]["en"], pt_br_by_index, entry["index"]),
        )

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

        for prof_index in race_grants.get(entry["index"], []):
            session.add(
                ProficiencyRace(
                    id=uuid.uuid4(),
                    proficiency_id=proficiencies_by_index[prof_index],
                    race_id=race.id,
                )
            )

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


# --- Classes (PRD §7.4.4) ---------------------------------------------------


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
    if await session.scalar(select(ClassDefinition).limit(1)) is not None:
        return

    proficiencies_by_index = await _index_map(session, Proficiency)
    class_grants, _ = await _seed_proficiency_grants(session, proficiencies_by_index)

    data = _load("classes")
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

        for prof_index in class_grants.get(entry["index"], []):
            session.add(
                ProficiencyClass(
                    id=uuid.uuid4(),
                    proficiency_id=proficiencies_by_index[prof_index],
                    class_definition_id=cls.id,
                )
            )

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


# --- Spells (PRD §7.4.5) ----------------------------------------------------


async def _seed_spells(session: AsyncSession) -> None:
    if await session.scalar(select(Spell).limit(1)) is not None:
        return

    schools_by_index = await _index_map(session, MagicSchool)
    classes_by_index = await _index_map(session, ClassDefinition)

    data = _load("spells")
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


# --- Items / equipment (PRD §7.4.6) -----------------------------------------


async def _seed_items(session: AsyncSession) -> None:
    if await session.scalar(select(Item).limit(1)) is not None:
        return

    categories_by_index = await _index_map(session, EquipmentCategory)
    properties_by_index = await _index_map(session, WeaponProperty)
    damage_types_by_index = await _index_map(session, DamageType)

    data = _load("items")
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


async def _seed_magic_items(session: AsyncSession) -> None:
    if await session.scalar(select(MagicItem).limit(1)) is not None:
        return

    categories_by_index = await _index_map(session, EquipmentCategory)

    data = _load("magic_items")
    #: Every entry (base or variant) is a top-level row in `magic_items.json`
    #: already (see `convert_srd.convert_magic_items`) — two passes so a
    #: variant's `variant_of_id` can resolve against its already-created base.
    by_index: dict[str, uuid.UUID] = {}
    for entry in data:
        if entry["is_variant"]:
            continue
        magic_item = MagicItem(
            id=uuid.uuid4(),
            index=entry["index"],
            equipment_category_id=categories_by_index[entry["equipment_category_index"]],
            rarity=entry["rarity"],
            is_custom=False,
            is_variant=False,
            variant_of_id=None,
        )
        session.add(magic_item)
        by_index[entry["index"]] = magic_item.id
        await _seed_i18n(session, MagicItemI18n, magic_item.id, entry["i18n"])

    for entry in data:
        if not entry["is_variant"]:
            continue
        base_id = by_index.get(entry["variant_of_index"] or "")
        magic_item = MagicItem(
            id=uuid.uuid4(),
            index=entry["index"],
            equipment_category_id=categories_by_index[entry["equipment_category_index"]],
            rarity=entry["rarity"],
            is_custom=False,
            is_variant=True,
            variant_of_id=base_id,
        )
        session.add(magic_item)
        await _seed_i18n(session, MagicItemI18n, magic_item.id, entry["i18n"])


# --- Backgrounds / feats (PRD §7.4.7) ---------------------------------------


async def _seed_backgrounds(session: AsyncSession) -> None:
    if await session.scalar(select(Background).limit(1)) is not None:
        return

    items_by_index = await _index_map(session, Item)
    proficiencies_by_index = await _index_map(session, Proficiency)
    pt_br_by_index = _load_pt_br("backgrounds")
    #: `pt_br_by_index[index]` nests its own "feature" translation (matched
    #: separately below, against `BackgroundFeatureI18n`) — excluded here so
    #: it isn't passed as a `BackgroundI18n` constructor kwarg.
    background_pt_br_by_index = {
        index: {k: v for k, v in fields.items() if k != "feature"}
        for index, fields in pt_br_by_index.items()
    }

    data = _load("backgrounds")
    for entry in data:
        background = Background(id=uuid.uuid4(), index=entry["index"], is_custom=False)
        session.add(background)
        await _seed_i18n(
            session,
            BackgroundI18n,
            background.id,
            _translations(
                entry["i18n"]["en"], background_pt_br_by_index, entry["index"]
            ),
        )

        for prof_index in entry.get("proficiency_indexes", []):
            proficiency_id = proficiencies_by_index.get(prof_index)
            if proficiency_id is not None:
                session.add(
                    BackgroundProficiency(
                        id=uuid.uuid4(),
                        background_id=background.id,
                        proficiency_id=proficiency_id,
                    )
                )

        for grant in entry.get("equipment", []):
            item_id = items_by_index.get(grant["item_index"])
            if item_id is not None:
                session.add(
                    BackgroundEquipment(
                        id=uuid.uuid4(),
                        background_id=background.id,
                        item_id=item_id,
                        quantity=grant["quantity"],
                    )
                )

        if feature_i18n := entry.get("feature"):
            feature = BackgroundFeature(id=uuid.uuid4(), background_id=background.id)
            session.add(feature)
            translations = dict(feature_i18n)
            pt_br_feature = (pt_br_by_index.get(entry["index"]) or {}).get("feature")
            if pt_br_feature:
                translations["pt-BR"] = pt_br_feature
            await _seed_i18n(session, BackgroundFeatureI18n, feature.id, translations)


async def _seed_feats(session: AsyncSession) -> None:
    if await session.scalar(select(Feat).limit(1)) is not None:
        return

    ability_scores_by_index = await _index_map(session, AbilityScoreDefinition)
    pt_br_by_index = _load_pt_br("feats")

    data = _load("feats")
    for entry in data:
        feat = Feat(id=uuid.uuid4(), index=entry["index"], is_custom=False)
        session.add(feat)
        await _seed_i18n(
            session,
            FeatI18n,
            feat.id,
            _translations(entry["i18n"]["en"], pt_br_by_index, entry["index"]),
        )

        for prereq in entry.get("prerequisites", []):
            session.add(
                FeatPrerequisite(
                    id=uuid.uuid4(),
                    feat_id=feat.id,
                    ability_score_id=ability_scores_by_index.get(
                        prereq["ability_score_index"]
                    ),
                    minimum_score=prereq["minimum_score"],
                )
            )


# --- Monsters (PRD §7.4.8) --------------------------------------------------


def _seed_monster_actions(
    session: AsyncSession,
    monster_id: uuid.UUID,
    action_model: Any,
    damage_model: Any,
    entries: list[dict[str, Any]],
    *,
    ability_scores_by_index: dict[str, uuid.UUID],
    damage_types_by_index: dict[str, uuid.UUID],
) -> None:
    """Seed one of the four action-shaped lists (actions/legendary/reactions/specials).

    `action_model`/`damage_model` are the matching pair for that list (e.g.
    `MonsterAction`/`MonsterActionDamage`) — same shape, different tables per
    PRD §7.4.8 instead of a generic polymorphic reference.
    """
    for entry in entries:
        save_index = entry.get("save_ability_score_index")
        action = action_model(
            id=uuid.uuid4(),
            monster_id=monster_id,
            name=entry["name"],
            description=entry["description"],
            attack_bonus=entry.get("attack_bonus"),
            save_ability_score_id=(
                ability_scores_by_index.get(save_index) if save_index else None
            ),
            save_dc=entry.get("save_dc"),
            usage_type=entry.get("usage_type"),
            usage_times=entry.get("usage_times"),
        )
        session.add(action)
        for dmg in entry.get("damages", []):
            session.add(
                damage_model(
                    id=uuid.uuid4(),
                    action_id=action.id,
                    damage_dice=dmg["damage_dice"],
                    damage_type_id=damage_types_by_index[dmg["damage_type_index"]],
                )
            )


async def _seed_monsters(session: AsyncSession) -> None:
    if await session.scalar(select(Monster).limit(1)) is not None:
        return

    ability_scores_by_index = await _index_map(session, AbilityScoreDefinition)
    damage_types_by_index = await _index_map(session, DamageType)
    proficiencies_by_index = await _index_map(session, Proficiency)
    conditions_by_index = await _index_map(session, Condition)

    data = _load("monsters")
    for entry in data:
        monster = Monster(
            id=uuid.uuid4(),
            index=entry["index"],
            size=entry["size"],
            creature_type=entry["creature_type"],
            creature_subtype=entry.get("creature_subtype"),
            alignment=entry["alignment"],
            hit_points=entry["hit_points"],
            hit_dice=entry["hit_dice"],
            challenge_rating=entry["challenge_rating"],
            xp=entry["xp"],
            proficiency_bonus=entry.get("proficiency_bonus"),
            languages=entry.get("languages", ""),
            strength=entry["strength"],
            dexterity=entry["dexterity"],
            constitution=entry["constitution"],
            intelligence=entry["intelligence"],
            wisdom=entry["wisdom"],
            charisma=entry["charisma"],
            is_custom=False,
        )
        session.add(monster)
        await _seed_i18n(session, MonsterI18n, monster.id, entry["i18n"])

        if speed := entry.get("speed"):
            session.add(
                MonsterSpeed(
                    id=uuid.uuid4(),
                    monster_id=monster.id,
                    walk=speed.get("walk"),
                    burrow=speed.get("burrow"),
                    climb=speed.get("climb"),
                    fly=speed.get("fly"),
                    swim=speed.get("swim"),
                    hover=speed.get("hover", False),
                )
            )

        if senses := entry.get("senses"):
            session.add(
                MonsterSense(
                    id=uuid.uuid4(),
                    monster_id=monster.id,
                    passive_perception=senses["passive_perception"],
                    blindsight=senses.get("blindsight"),
                    darkvision=senses.get("darkvision"),
                    tremorsense=senses.get("tremorsense"),
                    truesight=senses.get("truesight"),
                )
            )

        for ac in entry.get("armor_classes", []):
            session.add(
                MonsterArmorClass(
                    id=uuid.uuid4(),
                    monster_id=monster.id,
                    ac_type=ac["ac_type"],
                    value=ac["value"],
                    condition_id=None,
                    description=ac.get("description"),
                )
            )

        for prof in entry.get("proficiencies", []):
            proficiency_id = proficiencies_by_index.get(prof["proficiency_index"])
            if proficiency_id is not None:
                session.add(
                    MonsterProficiency(
                        id=uuid.uuid4(),
                        monster_id=monster.id,
                        proficiency_id=proficiency_id,
                        value=prof["value"],
                    )
                )

        for dm in entry.get("damage_modifiers", []):
            session.add(
                MonsterDamageModifier(
                    id=uuid.uuid4(),
                    monster_id=monster.id,
                    damage_type_id=damage_types_by_index[dm["damage_type_index"]],
                    modifier_type=dm["modifier_type"],
                )
            )

        for condition_index in entry.get("condition_immunities", []):
            condition_id = conditions_by_index.get(condition_index)
            if condition_id is not None:
                session.add(
                    MonsterConditionImmunity(
                        id=uuid.uuid4(),
                        monster_id=monster.id,
                        condition_id=condition_id,
                    )
                )

        for list_key, action_model, damage_model in (
            ("actions", MonsterAction, MonsterActionDamage),
            ("legendary_actions", MonsterLegendaryAction, MonsterLegendaryActionDamage),
            ("reactions", MonsterReaction, MonsterReactionDamage),
            ("special_abilities", MonsterSpecialAbility, MonsterSpecialAbilityDamage),
        ):
            _seed_monster_actions(
                session,
                monster.id,
                action_model,
                damage_model,
                entry.get(list_key, []),
                ability_scores_by_index=ability_scores_by_index,
                damage_types_by_index=damage_types_by_index,
            )


# --- Rules (PRD §7.4.9) -----------------------------------------------------


async def _seed_rules(session: AsyncSession) -> None:
    if await session.scalar(select(RuleSection).limit(1)) is not None:
        return

    data = _load("rules")
    #: Only the 6 top-level sections have a pt-BR translation — the 33
    #: fine-grained `Rule` entries below have no `_data/2014/pt-BR` source
    #: (see `convert_srd.convert_rules_pt_br`) and keep falling back to `en`.
    pt_br_by_index = _load_pt_br("rules")

    sections_by_index: dict[str, uuid.UUID] = {}
    for entry in data["sections"]:
        section = RuleSection(id=uuid.uuid4(), index=entry["index"], is_custom=False)
        session.add(section)
        await _seed_i18n(
            session,
            RuleSectionI18n,
            section.id,
            _translations(entry["i18n"]["en"], pt_br_by_index, entry["index"]),
        )
        sections_by_index[entry["index"]] = section.id

    for entry in data["rules"]:
        rule = Rule(id=uuid.uuid4(), index=entry["index"], is_custom=False)
        session.add(rule)
        await _seed_i18n(session, RuleI18n, rule.id, entry["i18n"])

        for section_index in entry.get("section_indexes", []):
            session.add(
                RuleRuleSection(
                    id=uuid.uuid4(),
                    rule_id=rule.id,
                    rule_section_id=sections_by_index[section_index],
                )
            )
