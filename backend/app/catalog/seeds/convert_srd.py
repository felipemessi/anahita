"""One-off script: convert `_data/2014/en/*.json` into `seed.py`'s data shape.

Converts the SRD APIReference format into the normalized
`backend/app/catalog/seeds/data/*.json` shape `seed.py` reads.

Why a pre-generation step instead of teaching `seed.py` to read the raw SRD
JSON directly at runtime: the raw files use API-reference conventions (nested
`{"index", "name", "url"}` references, free-text stat blocks, inconsistent
per-category shapes) that need real resolution logic (index -> FK, unit
conversion, prerequisite parsing). Doing that once here and committing the
normalized output keeps `seed.py` a plain, reviewable "insert this data"
script — same shape it already had for the placeholder fixtures — and keeps
the raw-format knowledge in one place instead of smeared across every
`_seed_*` function. Re-run this script (`uv run python -m
app.catalog.seeds.convert_srd`) whenever `_data/2014` changes; it is not
imported by the app at runtime.

Run from the `backend/` directory (or anywhere — paths are resolved from this
file's location) with no arguments.
"""

import json
import re
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[4]
_SRC_DIR = _REPO_ROOT / "_data" / "2014" / "en"
_OUT_DIR = Path(__file__).parent / "data"


def _load(name: str) -> Any:
    return json.loads((_SRC_DIR / f"5e-SRD-{name}.json").read_text())


def _write(name: str, data: Any) -> None:
    (_OUT_DIR / f"{name}.json").write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    )


def _desc(entry: dict[str, Any], key: str = "desc") -> str:
    """Join SRD `desc` (a paragraph list, or a plain string) into one string."""
    val = entry.get(key)
    if val is None:
        return ""
    if isinstance(val, list):
        return "\n\n".join(val)
    return str(val)


def _cost_in_cp(entry: dict[str, Any]) -> int:
    """Convert a `{"quantity": N, "unit": "gp"}` cost to copper pieces (the DB unit)."""
    cost = entry.get("cost")
    if not cost:
        return 0
    rate = {"cp": 1, "sp": 10, "ep": 50, "gp": 100, "pp": 1000}[cost["unit"]]
    return int(cost["quantity"]) * rate


# --- Fixed vocabulary (PRD §7.4.1) ------------------------------------------


def convert_ability_scores() -> None:
    """Write `ability_scores.json` from `5e-SRD-Ability-Scores.json`."""
    data = _load("Ability-Scores")
    out = [
        {
            "index": e["index"],
            "name": e["name"],
            "full_name": e["full_name"],
            "desc": _desc(e),
        }
        for e in data
    ]
    _write("ability_scores", out)


def convert_skills() -> None:
    """Write `skills.json` from `5e-SRD-Skills.json`."""
    data = _load("Skills")
    out = [
        {
            "index": e["index"],
            "name": e["name"],
            "desc": _desc(e),
            "ability_score_index": e["ability_score"]["index"],
        }
        for e in data
    ]
    _write("skills", out)


def convert_alignments() -> None:
    """Write `alignments.json` from `5e-SRD-Alignments.json`."""
    data = _load("Alignments")
    out = [
        {
            "index": e["index"],
            "name": e["name"],
            "abbreviation": e["abbreviation"],
            "desc": _desc(e),
        }
        for e in data
    ]
    _write("alignments", out)


def convert_conditions() -> None:
    """Write `conditions.json` from `5e-SRD-Conditions.json`."""
    data = _load("Conditions")
    out = [{"index": e["index"], "name": e["name"], "desc": _desc(e)} for e in data]
    _write("conditions", out)


def convert_damage_types() -> None:
    """Write `damage_types.json` from `5e-SRD-Damage-Types.json`."""
    data = _load("Damage-Types")
    out = [{"index": e["index"], "name": e["name"], "desc": _desc(e)} for e in data]
    _write("damage_types", out)


def convert_magic_schools() -> None:
    """Write `magic_schools.json` from `5e-SRD-Magic-Schools.json`."""
    data = _load("Magic-Schools")
    out = [{"index": e["index"], "name": e["name"], "desc": _desc(e)} for e in data]
    _write("magic_schools", out)


def convert_languages() -> None:
    """Write `languages.json` from `5e-SRD-Languages.json`."""
    data = _load("Languages")
    out = [
        {
            "index": e["index"],
            "name": e["name"],
            "desc": _desc(e),
            "script": e.get("script"),
            "typical_speakers": ", ".join(e.get("typical_speakers", [])) or None,
            "language_type": e["type"].lower(),
        }
        for e in data
    ]
    _write("languages", out)


def convert_weapon_properties() -> None:
    """Write `weapon_properties.json` from `5e-SRD-Weapon-Properties.json`."""
    data = _load("Weapon-Properties")
    out = [{"index": e["index"], "name": e["name"], "desc": _desc(e)} for e in data]
    _write("weapon_properties", out)


def convert_equipment_categories() -> None:
    """Write `equipment_categories.json` from `5e-SRD-Equipment-Categories.json`."""
    data = _load("Equipment-Categories")
    out = [{"index": e["index"], "name": e["name"]} for e in data]
    _write("equipment_categories", out)


#: A Proficiency's `index` -> its type bucket. `skill-*`/`saving-throw-*`
#: entries resolve to a SkillDefinition/AbilityScoreDefinition FK by stripping
#: their prefix; the raw `type` field only tells us "Skills" vs "Saving
#: Throws" vs everything else, so we branch on the index shape instead.
_SAVING_THROW_PREFIX = "saving-throw-"
_SKILL_PREFIX = "skill-"
#: Raw `type` -> (ProficiencyType, ...) for the remaining buckets. Only
#: proficiencies whose `index` matches an EquipmentCategory index get a real
#: `equipment_category_id` (the CHECK constraint requires it for
#: weapon/armor/tool); everything else (individual weapons/tools/instruments,
#: e.g. "battleaxe", "thieves-tools") falls back to `other` — still stored,
#: just without a specific equipment-category link.
_CATEGORY_BACKED_TYPES = {
    "Armor": "armor",
    "Weapons": "weapon",
    "Vehicles": "tool",
    "Artisan's Tools": "tool",
    "Gaming Sets": "tool",
    "Musical Instruments": "tool",
}


def convert_proficiencies() -> None:
    """Write `proficiencies.json` from `5e-SRD-Proficiencies.json`."""
    data = _load("Proficiencies")
    categories = {c["index"] for c in _load("Equipment-Categories")}
    out = []
    for e in data:
        index = e["index"]
        if index.startswith(_SKILL_PREFIX):
            proficiency_type = "skill"
            skill_index: str | None = index[len(_SKILL_PREFIX) :]
            ability_score_index = None
            equipment_category_index = None
        elif index.startswith(_SAVING_THROW_PREFIX):
            proficiency_type = "saving_throw"
            skill_index = None
            ability_score_index = index[len(_SAVING_THROW_PREFIX) :]
            equipment_category_index = None
        elif index in categories and e["type"] in _CATEGORY_BACKED_TYPES:
            proficiency_type = _CATEGORY_BACKED_TYPES[e["type"]]
            skill_index = None
            ability_score_index = None
            equipment_category_index = index
        else:
            proficiency_type = "other"
            skill_index = None
            ability_score_index = None
            equipment_category_index = None

        out.append(
            {
                "index": index,
                "name": e["name"],
                "proficiency_type": proficiency_type,
                "skill_index": skill_index,
                "ability_score_index": ability_score_index,
                "equipment_category_index": equipment_category_index,
                "class_indexes": [c["index"] for c in e.get("classes", [])],
                "race_indexes": [r["index"] for r in e.get("races", [])],
            }
        )
    _write("proficiencies", out)


# --- Races (PRD §7.4.2) -----------------------------------------------------

#: All 2014-SRD races/subraces with the Darkvision trait get 60 ft (no
#: "superior" 120 ft variant is present in this dataset) — the raw format
#: only lists the trait by reference, not a numeric range.
_DARKVISION_RANGE_FT = 60


def _race_ability_bonuses(entry: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {"ability": ab["ability_score"]["index"], "bonus": ab["bonus"]}
        for ab in entry.get("ability_bonuses", [])
    ]


def _trait_entries(
    trait_refs: list[dict[str, Any]], traits_by_index: dict[str, Any]
) -> list[dict[str, Any]]:
    out = []
    for ref in trait_refs:
        trait = traits_by_index[ref["index"]]
        out.append(
            {
                "mechanical_effect": None,
                "i18n": {
                    "en": {
                        "trait_name": trait["name"],
                        "description": _desc(trait),
                    }
                },
            }
        )
    return out


def convert_races() -> None:
    """Write `races.json` from `5e-SRD-Races.json`/`Subraces.json`/`Traits.json`."""
    races = _load("Races")
    subraces = _load("Subraces")
    traits = _load("Traits")
    traits_by_index = {t["index"]: t for t in traits}
    subraces_by_race: dict[str, list[dict[str, Any]]] = {}
    for sr in subraces:
        subraces_by_race.setdefault(sr["race"]["index"], []).append(sr)

    out = []
    for race in races:
        has_darkvision = any(t["index"] == "darkvision" for t in race.get("traits", []))
        entry = {
            "index": race["index"],
            "speed": race["speed"],
            "size": race["size"].lower(),
            "darkvision_range": _DARKVISION_RANGE_FT if has_darkvision else 0,
            "i18n": {
                "en": {
                    "name": race["name"],
                    "description": _desc(race),
                    "age": race.get("age", ""),
                    "alignment_desc": race.get("alignment", ""),
                    "size_description": race.get("size_description", ""),
                    "language_desc": race.get("language_desc", ""),
                }
            },
            "ability_bonuses": _race_ability_bonuses(race),
            "traits": _trait_entries(race.get("traits", []), traits_by_index),
            "subraces": [],
        }
        for sr in subraces_by_race.get(race["index"], []):
            entry["subraces"].append(
                {
                    "index": sr["index"],
                    "i18n": {
                        "en": {"name": sr["name"], "description": _desc(sr)}
                    },
                    "ability_bonuses": [
                        {"ability": ab["ability_score"]["index"], "bonus": ab["bonus"]}
                        for ab in sr.get("ability_bonuses", [])
                    ],
                    "traits": _trait_entries(
                        sr.get("racial_traits", []), traits_by_index
                    ),
                }
            )
        out.append(entry)
    _write("races", out)


# --- Classes (PRD §7.4.4) ---------------------------------------------------

#: Not present in the SRD API (it's a wiki/UX convenience, not game data) —
#: fixed for the 12 SRD 2014 classes.
_PRIMARY_ABILITY = {
    "barbarian": "Strength",
    "bard": "Charisma",
    "cleric": "Wisdom",
    "druid": "Wisdom",
    "fighter": "Strength or Dexterity",
    "monk": "Dexterity and Wisdom",
    "paladin": "Strength and Charisma",
    "ranger": "Dexterity and Wisdom",
    "rogue": "Dexterity",
    "sorcerer": "Charisma",
    "warlock": "Charisma",
    "wizard": "Intelligence",
}

_ABILITY_FULL_NAME = {
    "str": "Strength",
    "dex": "Dexterity",
    "con": "Constitution",
    "int": "Intelligence",
    "wis": "Wisdom",
    "cha": "Charisma",
}


def _feature_entry(feature: dict[str, Any]) -> dict[str, Any]:
    prereqs = []
    for p in feature.get("prerequisites", []):
        if p["type"] == "level":
            prereqs.append({"prerequisite_type": "level", "level": p["level"]})
        elif p["type"] == "feature":
            required_index = p["feature"].rsplit("/", 1)[-1]
            prereqs.append(
                {
                    "prerequisite_type": "feature",
                    "required_feature_index": required_index,
                }
            )
        elif p["type"] == "spell":
            # Not resolved here: FeaturePrerequisite.spell_id needs the Spell
            # seeded first, and classes seed before spells (spells need
            # ClassDefinition ids for SpellClass). Left unlinked — the
            # prerequisite type is still recorded as free text isn't modeled,
            # so this one prerequisite kind is dropped rather than seeded
            # half-resolved.
            continue
    return {
        "index": feature["index"],
        "level": feature["level"],
        "mechanical_effect": None,
        "i18n": {
            "en": {"feature_name": feature["name"], "description": _desc(feature)}
        },
        "prerequisites": prereqs,
    }


def convert_classes() -> None:
    """Write `classes.json` from Classes/Subclasses/Features/Levels."""
    classes = _load("Classes")
    subclasses = _load("Subclasses")
    features = _load("Features")
    levels = _load("Levels")

    features_by_class: dict[str, list[dict[str, Any]]] = {}
    features_by_subclass: dict[str, list[dict[str, Any]]] = {}
    for f in features:
        if "subclass" in f:
            features_by_subclass.setdefault(f["subclass"]["index"], []).append(f)
        else:
            features_by_class.setdefault(f["class"]["index"], []).append(f)

    subclasses_by_class: dict[str, list[dict[str, Any]]] = {}
    for sc in subclasses:
        subclasses_by_class.setdefault(sc["class"]["index"], []).append(sc)

    base_levels_by_class: dict[str, list[dict[str, Any]]] = {}
    for lvl in levels:
        if "subclass" not in lvl:
            base_levels_by_class.setdefault(lvl["class"]["index"], []).append(lvl)

    out = []
    for cls in classes:
        idx = cls["index"]
        saving_throws = ", ".join(
            _ABILITY_FULL_NAME[st["index"]] for st in cls.get("saving_throws", [])
        )
        class_levels = []
        for lvl in sorted(base_levels_by_class.get(idx, []), key=lambda x: x["level"]):
            spell_slots = []
            spellcasting = lvl.get("spellcasting") or {}
            if "cantrips_known" in spellcasting:
                spell_slots.append(
                    {"spell_level": 0, "slot_count": spellcasting["cantrips_known"]}
                )
            for key, value in spellcasting.items():
                match = re.fullmatch(r"spell_slots_level_(\d)", key)
                if match and value:
                    spell_slots.append(
                        {"spell_level": int(match.group(1)), "slot_count": value}
                    )
            resources = [
                {"resource_key": key, "value": str(value)}
                for key, value in lvl.get("class_specific", {}).items()
                # `ClassLevelResource.value` is a short scalar (PRD §8.3:
                # "3", "2d6") — a few class_specific entries are themselves
                # tables (Sorcerer's per-level Metamagic spell-slot-to-
                # sorcery-point conversion costs) that don't fit that shape
                # and would overflow the column. Dropped rather than
                # truncated/misrepresented.
                if not isinstance(value, list | dict)
            ]
            class_levels.append(
                {
                    "level": lvl["level"],
                    "proficiency_bonus": lvl.get("prof_bonus"),
                    "ability_score_bonuses": lvl.get("ability_score_bonuses") or None,
                    "spell_slots": spell_slots,
                    "resources": resources,
                }
            )

        entry = {
            "index": idx,
            "hit_die": cls["hit_die"],
            "primary_ability": _PRIMARY_ABILITY.get(idx, saving_throws),
            "saving_throw_proficiencies": saving_throws,
            "i18n": {"en": {"name": cls["name"]}},
            "class_levels": class_levels,
            "features": [_feature_entry(f) for f in features_by_class.get(idx, [])],
            "subclasses": [],
        }
        for sc in subclasses_by_class.get(idx, []):
            entry["subclasses"].append(
                {
                    "index": sc["index"],
                    "i18n": {
                        "en": {
                            "name": sc["name"],
                            "description": _desc(sc),
                            "flavor": sc.get("subclass_flavor", ""),
                        }
                    },
                    "features": [
                        _feature_entry(f)
                        for f in features_by_subclass.get(sc["index"], [])
                    ],
                }
            )
        out.append(entry)
    _write("classes", out)


# --- Spells (PRD §7.4.5) ----------------------------------------------------


def convert_spells() -> None:
    """Write `spells.json` from `5e-SRD-Spells.json`."""
    data = _load("Spells")
    out = []
    for e in data:
        higher = e.get("higher_level")
        out.append(
            {
                "index": e["index"],
                "level": e["level"],
                "magic_school_index": e["school"]["index"],
                "casting_time": e["casting_time"],
                "range": e["range"],
                "duration": e["duration"],
                "components": ", ".join(e.get("components", [])),
                "ritual": e["ritual"],
                "concentration": e["concentration"],
                "i18n": {
                    "en": {
                        "name": e["name"],
                        "description": _desc(e),
                        "higher_levels": _desc({"desc": higher}) if higher else None,
                    }
                },
                "classes": [c["index"] for c in e.get("classes", [])],
            }
        )
    _write("spells", out)


# --- Items / equipment (PRD §7.4.6) -----------------------------------------

_ITEM_TYPE_BY_CATEGORY = {
    "weapon": "weapon",
    "armor": "armor",
    "adventuring-gear": "gear",
    "tools": "tool",
    "mounts-and-vehicles": "gear",
}


def convert_items() -> None:
    """Write `items.json` from `5e-SRD-Equipment.json`."""
    data = _load("Equipment")
    out = []
    for e in data:
        category_index = e["equipment_category"]["index"]
        item_type = _ITEM_TYPE_BY_CATEGORY.get(category_index)
        if item_type is None:
            continue

        entry: dict[str, Any] = {
            "index": e["index"],
            "item_type": item_type,
            "equipment_category_index": category_index,
            "rarity": None,
            "weight": float(e.get("weight", 0) or 0),
            "cost": _cost_in_cp(e),
            "i18n": {"en": {"name": e["name"], "description": _desc(e)}},
            "properties": [p["index"] for p in e.get("properties", [])],
        }

        damage = e.get("damage")
        if damage:
            entry["weapon_detail"] = {
                "damage_dice": damage["damage_dice"],
                "damage_type_index": damage["damage_type"]["index"],
                "weapon_range": e.get("weapon_range", "Melee"),
            }

        if "armor_class" in e:
            ac = e["armor_class"]
            entry["armor_detail"] = {
                "base_ac": ac["base"],
                "dex_bonus_cap": ac.get("max_bonus"),
                "stealth_disadvantage": e.get("stealth_disadvantage", False),
                "strength_requirement": e.get("str_minimum") or None,
            }

        out.append(entry)
    _write("items", out)


# --- Magic items (PRD §7.4.6) -----------------------------------------------


def convert_magic_items() -> None:
    """Write `magic_items.json` from `5e-SRD-Magic-Items.json`."""
    data = _load("Magic-Items")
    #: Reverse map built from every base entry's `variants` list: a variant's
    #: index -> its base item's index. Variants are *also* top-level entries
    #: in this file (with `variant: true`), so they are not re-created here —
    #: only linked back to their base via `variant_of_id`.
    base_index_by_variant_index: dict[str, str] = {}
    for e in data:
        for v in e.get("variants", []):
            base_index_by_variant_index[v["index"]] = e["index"]

    out = []
    for e in data:
        out.append(
            {
                "index": e["index"],
                "equipment_category_index": e["equipment_category"]["index"],
                "rarity": e["rarity"]["name"].lower().replace(" ", "_"),
                "is_variant": e.get("variant", False),
                "variant_of_index": base_index_by_variant_index.get(e["index"]),
                "i18n": {"en": {"name": e["name"], "description": _desc(e)}},
            }
        )
    _write("magic_items", out)


# --- Backgrounds / feats (PRD §7.4.7) ---------------------------------------


def _roll_table_text(table: dict[str, Any]) -> str:
    """Join a Background roll-table's options into descriptive text.

    `BackgroundI18n` stores these as free text rather than a rollable table
    (see its docstring in models.py) — each option (a `string`, or an `ideal`
    with its own `desc`) becomes one " / "-separated line.
    """
    options = table.get("from", {}).get("options", [])
    lines = [o.get("string") or o.get("desc", "") for o in options]
    return " / ".join(line for line in lines if line)


def convert_backgrounds() -> None:
    """Write `backgrounds.json` from `5e-SRD-Backgrounds.json`."""
    data = _load("Backgrounds")
    out = []
    for e in data:
        feature = e.get("feature")
        out.append(
            {
                "index": e["index"],
                "i18n": {
                    "en": {
                        "name": e["name"],
                        "personality_traits": _roll_table_text(
                            e.get("personality_traits", {})
                        ),
                        "ideals": _roll_table_text(e.get("ideals", {})),
                        "bonds": _roll_table_text(e.get("bonds", {})),
                        "flaws": _roll_table_text(e.get("flaws", {})),
                    }
                },
                "proficiency_indexes": [
                    p["index"] for p in e.get("starting_proficiencies", [])
                ],
                "equipment": [
                    {"item_index": eq["equipment"]["index"], "quantity": eq["quantity"]}
                    for eq in e.get("starting_equipment", [])
                ],
                "feature": (
                    {
                        "en": {
                            "feature_name": feature["name"],
                            "description": _desc(feature),
                        }
                    }
                    if feature
                    else None
                ),
            }
        )
    _write("backgrounds", out)


def convert_feats() -> None:
    """Write `feats.json` from `5e-SRD-Feats.json`."""
    data = _load("Feats")
    out = []
    for e in data:
        out.append(
            {
                "index": e["index"],
                "i18n": {"en": {"name": e["name"], "description": _desc(e)}},
                "prerequisites": [
                    {
                        "ability_score_index": p["ability_score"]["index"],
                        "minimum_score": p["minimum_score"],
                    }
                    for p in e.get("prerequisites", [])
                ],
            }
        )
    _write("feats", out)


# --- Monsters (PRD §7.4.8) --------------------------------------------------

#: Damage vulnerability/resistance/immunity strings are sometimes compound
#: and conditional ("bludgeoning, piercing, and slashing from nonmagical
#: weapons") — `MonsterDamageModifier` only models a clean damage-type FK, no
#: qualifier. Every clean damage-type word found in the string becomes its
#: own row; the qualifier itself (e.g. "from nonmagical weapons") is dropped.
_DAMAGE_TYPE_WORDS = (
    "acid",
    "bludgeoning",
    "cold",
    "fire",
    "force",
    "lightning",
    "necrotic",
    "piercing",
    "poison",
    "psychic",
    "radiant",
    "slashing",
    "thunder",
)


def _damage_type_indexes_in(text: str) -> list[str]:
    lowered = text.lower()
    return [w for w in _DAMAGE_TYPE_WORDS if re.search(rf"\b{w}\b", lowered)]


def _sense_range(value: str | None) -> str | None:
    """Trim a sense range to fit `String(50)`.

    Every SRD sense range is "N ft." except grimlock's blindsight, which adds
    a "(blind beyond this radius)" qualifier that overflows the column —
    dropped, keeping just the leading range.
    """
    if value and len(value) > 50:
        return value.split(" or ")[0].split(" (")[0]
    return value


def _monster_action_entry(a: dict[str, Any]) -> dict[str, Any]:
    dc = a.get("dc")
    usage = a.get("usage") or {}
    return {
        "name": a["name"],
        "description": a.get("desc", ""),
        "attack_bonus": a.get("attack_bonus"),
        "save_ability_score_index": dc["dc_type"]["index"] if dc else None,
        "save_dc": dc["dc_value"] if dc else None,
        "usage_type": usage.get("type"),
        "usage_times": usage.get("times"),
        "damages": [
            {
                "damage_dice": d["damage_dice"],
                "damage_type_index": d["damage_type"]["index"],
            }
            for d in a.get("damage", [])
            # A few actions offer a damage-type *choice* ("lightning or
            # thunder, attacker's choice") instead of a fixed roll — modeled
            # as a `choose`/`from` block with no `damage_dice`/`damage_type`
            # of its own. Not representable as a single MonsterActionDamage
            # row, so skipped; the fixed rolls on the same action still seed.
            if "damage_dice" in d and "damage_type" in d
        ],
    }


def convert_monsters() -> None:
    """Write `monsters.json` from `5e-SRD-Monsters.json`."""
    data = _load("Monsters")
    out = []
    for m in data:
        proficiencies_by_index: dict[str, int] = {}
        for p in m.get("proficiencies", []):
            proficiencies_by_index[p["proficiency"]["index"]] = p["value"]
        proficiencies = [
            {"proficiency_index": index, "value": value}
            for index, value in proficiencies_by_index.items()
        ]

        # `dict.fromkeys` dedupes while preserving order: a couple of
        # monsters repeat the same condition/damage-type-word across two
        # compound strings (e.g. two resistance clauses both mentioning
        # "poison"), which would otherwise violate the DB's uniqueness
        # constraints on these junctions.
        damage_modifier_pairs = dict.fromkeys(
            (dt_index, modifier_type)
            for modifier_type, key in (
                ("vulnerable", "damage_vulnerabilities"),
                ("resistant", "damage_resistances"),
                ("immune", "damage_immunities"),
            )
            for text in m.get(key, [])
            for dt_index in _damage_type_indexes_in(text)
        )
        damage_modifiers = [
            {"damage_type_index": dt_index, "modifier_type": modifier_type}
            for dt_index, modifier_type in damage_modifier_pairs
        ]

        armor_classes = []
        for ac in m.get("armor_class", []):
            parts = [a["name"] for a in ac.get("armor", [])]
            armor_classes.append(
                {
                    "ac_type": ac["type"],
                    "value": ac["value"],
                    "description": ", ".join(parts) or ac.get("desc"),
                }
            )

        senses = m.get("senses", {})
        out.append(
            {
                "index": m["index"],
                "size": m["size"].lower(),
                "creature_type": m["type"],
                "creature_subtype": m.get("subtype"),
                "alignment": m["alignment"],
                "hit_points": m["hit_points"],
                "hit_dice": m["hit_dice"],
                "challenge_rating": m["challenge_rating"],
                "xp": m["xp"],
                "proficiency_bonus": m.get("proficiency_bonus"),
                "languages": m.get("languages", ""),
                "strength": m["strength"],
                "dexterity": m["dexterity"],
                "constitution": m["constitution"],
                "intelligence": m["intelligence"],
                "wisdom": m["wisdom"],
                "charisma": m["charisma"],
                "i18n": {"en": {"name": m["name"], "description": ""}},
                "speed": m.get("speed"),
                "senses": (
                    {
                        "passive_perception": senses.get("passive_perception", 10),
                        "blindsight": _sense_range(senses.get("blindsight")),
                        "darkvision": _sense_range(senses.get("darkvision")),
                        "tremorsense": _sense_range(senses.get("tremorsense")),
                        "truesight": _sense_range(senses.get("truesight")),
                    }
                    if senses
                    else None
                ),
                "armor_classes": armor_classes,
                "proficiencies": proficiencies,
                "damage_modifiers": damage_modifiers,
                "condition_immunities": list(
                    dict.fromkeys(c["index"] for c in m.get("condition_immunities", []))
                ),
                "actions": [_monster_action_entry(a) for a in m.get("actions", [])],
                "legendary_actions": [
                    _monster_action_entry(a) for a in m.get("legendary_actions", [])
                ],
                "reactions": [_monster_action_entry(a) for a in m.get("reactions", [])],
                "special_abilities": [
                    _monster_action_entry(a) for a in m.get("special_abilities", [])
                ],
            }
        )
    _write("monsters", out)


# --- Rules (PRD §7.4.9) -----------------------------------------------------
#
# Confusing but deliberate: the raw `Rules.json` (6 entries) holds the
# top-level topics (Combat, Adventuring, ...), each listing its finer-grained
# `subsections`; `Rule-Sections.json` (33 entries) holds those finer pieces.
# That's backwards from this app's naming — `RuleSection` is the top-level
# grouping and `Rule` is the individual entry (see `models.py`) — so
# `Rules.json` feeds `sections` below and `Rule-Sections.json` feeds `rules`.


def convert_rules() -> None:
    """Write `rules.json` from `5e-SRD-Rules.json`/`Rule-Sections.json`."""
    top_level = _load("Rules")
    fine_grained = _load("Rule-Sections")

    section_index_by_rule_index: dict[str, list[str]] = {}
    for section in top_level:
        for sub in section.get("subsections", []):
            section_index_by_rule_index.setdefault(sub["index"], []).append(
                section["index"]
            )

    out = {
        "sections": [
            {
                "index": s["index"],
                "i18n": {"en": {"name": s["name"], "desc": _desc(s)}},
            }
            for s in top_level
        ],
        "rules": [
            {
                "index": r["index"],
                "i18n": {"en": {"name": r["name"], "desc": _desc(r)}},
                "section_indexes": section_index_by_rule_index.get(r["index"], []),
            }
            for r in fine_grained
        ],
    }
    _write("rules", out)


# --- pt-BR partial translations ---------------------------------------------
#
# Only 12 of the 24 categories have a `_data/2014/pt-BR` file at all (no
# Classes/Spells/Equipment/Magic-Items/Monsters/Proficiencies/Traits/
# Subclasses/Subraces/Levels/Rule-Sections translation exists), and within a
# translated category some nested text simply isn't available either (e.g.
# Races.json lists each trait/subrace by `{index, name, url}` only — a
# translated *name*, but no translated description, since there's no pt-BR
# Traits.json/Subraces.json to source one from). `seed.py`'s i18n rows are
# whole-row, not per-field, so a partial row (translated name, empty
# description) would make a pt-BR reader see a blank description where `en`
# fallback would have shown real text — worse than not seeding that row at
# all. Each `convert_*_pt_br` below therefore only writes an index -> fields
# dict for entities where every field it carries has real pt-BR content;
# nested trait/subrace names present in `Races.json` but missing a
# description are left out of `races_pt_br.json`, on purpose.

_PT_BR_SRC_DIR = _REPO_ROOT / "_data" / "2014" / "pt-BR"


def _load_pt_br(name: str) -> Any:
    return json.loads((_PT_BR_SRC_DIR / f"5e-SRD-{name}.json").read_text())


def convert_ability_scores_pt_br() -> None:
    """Write `ability_scores_pt_br.json`: index -> translated fields."""
    out = {
        e["index"]: {"name": e["name"], "full_name": e["full_name"], "desc": _desc(e)}
        for e in _load_pt_br("Ability-Scores")
    }
    _write("ability_scores_pt_br", out)


def convert_skills_pt_br() -> None:
    """Write `skills_pt_br.json`: index -> translated fields."""
    out = {
        e["index"]: {"name": e["name"], "desc": _desc(e)}
        for e in _load_pt_br("Skills")
    }
    _write("skills_pt_br", out)


def convert_alignments_pt_br() -> None:
    """Write `alignments_pt_br.json`: index -> translated fields."""
    out = {
        e["index"]: {
            "name": e["name"],
            "abbreviation": e["abbreviation"],
            "desc": _desc(e),
        }
        for e in _load_pt_br("Alignments")
    }
    _write("alignments_pt_br", out)


def convert_conditions_pt_br() -> None:
    """Write `conditions_pt_br.json`: index -> translated fields."""
    out = {
        e["index"]: {"name": e["name"], "desc": _desc(e)}
        for e in _load_pt_br("Conditions")
    }
    _write("conditions_pt_br", out)


def convert_damage_types_pt_br() -> None:
    """Write `damage_types_pt_br.json`: index -> translated fields."""
    out = {
        e["index"]: {"name": e["name"], "desc": _desc(e)}
        for e in _load_pt_br("Damage-Types")
    }
    _write("damage_types_pt_br", out)


def convert_magic_schools_pt_br() -> None:
    """Write `magic_schools_pt_br.json`: index -> translated fields."""
    out = {
        e["index"]: {"name": e["name"], "desc": _desc(e)}
        for e in _load_pt_br("Magic-Schools")
    }
    _write("magic_schools_pt_br", out)


def convert_languages_pt_br() -> None:
    """Write `languages_pt_br.json`: index -> translated fields."""
    out = {
        e["index"]: {
            "name": e["name"],
            "desc": _desc(e),
            "script": e.get("script"),
            "typical_speakers": ", ".join(e.get("typical_speakers", [])) or None,
        }
        for e in _load_pt_br("Languages")
    }
    _write("languages_pt_br", out)


def convert_weapon_properties_pt_br() -> None:
    """Write `weapon_properties_pt_br.json`: index -> translated fields."""
    out = {
        e["index"]: {"name": e["name"], "desc": _desc(e)}
        for e in _load_pt_br("Weapon-Properties")
    }
    _write("weapon_properties_pt_br", out)


def convert_races_pt_br() -> None:
    """Write `races_pt_br.json`: index -> translated Race fields.

    Trait/subrace names are also translated in the source file (see the
    module docstring above) but are skipped here — no matching description.
    """
    out = {
        e["index"]: {
            "name": e["name"],
            "description": "",
            "age": e.get("age", ""),
            "alignment_desc": e.get("alignment", ""),
            "size_description": e.get("size_description", ""),
            "language_desc": e.get("language_desc", ""),
        }
        for e in _load_pt_br("Races")
    }
    _write("races_pt_br", out)


def convert_backgrounds_pt_br() -> None:
    """Write `backgrounds_pt_br.json`: index -> translated Background fields."""
    out = {}
    for e in _load_pt_br("Backgrounds"):
        feature = e.get("feature")
        out[e["index"]] = {
            "name": e["name"],
            "personality_traits": _roll_table_text(e.get("personality_traits", {})),
            "ideals": _roll_table_text(e.get("ideals", {})),
            "bonds": _roll_table_text(e.get("bonds", {})),
            "flaws": _roll_table_text(e.get("flaws", {})),
            "feature": (
                {"feature_name": feature["name"], "description": _desc(feature)}
                if feature
                else None
            ),
        }
    _write("backgrounds_pt_br", out)


def convert_feats_pt_br() -> None:
    """Write `feats_pt_br.json`: index -> translated Feat fields."""
    out = {
        e["index"]: {"name": e["name"], "description": _desc(e)}
        for e in _load_pt_br("Feats")
    }
    _write("feats_pt_br", out)


def convert_rules_pt_br() -> None:
    """Write `rules_pt_br.json`: index -> translated RuleSection fields.

    Only the 6 top-level sections (`Rules.json`, per the naming mismatch
    explained in `convert_rules`) have a pt-BR file — the 33 finer-grained
    `Rule` entries have no translation and keep falling back to `en`.
    """
    out = {
        e["index"]: {"name": e["name"], "desc": _desc(e)}
        for e in _load_pt_br("Rules")
    }
    _write("rules_pt_br", out)


def main() -> None:
    """Run every `convert_*` step: 18 `en` data files + 12 `_pt_br` ones."""
    convert_ability_scores()
    convert_skills()
    convert_alignments()
    convert_conditions()
    convert_damage_types()
    convert_magic_schools()
    convert_languages()
    convert_weapon_properties()
    convert_equipment_categories()
    convert_proficiencies()
    convert_races()
    convert_classes()
    convert_spells()
    convert_items()
    convert_magic_items()
    convert_backgrounds()
    convert_feats()
    convert_monsters()
    convert_rules()

    convert_ability_scores_pt_br()
    convert_skills_pt_br()
    convert_alignments_pt_br()
    convert_conditions_pt_br()
    convert_damage_types_pt_br()
    convert_magic_schools_pt_br()
    convert_languages_pt_br()
    convert_weapon_properties_pt_br()
    convert_races_pt_br()
    convert_backgrounds_pt_br()
    convert_feats_pt_br()
    convert_rules_pt_br()
    print("Converted SRD data into", _OUT_DIR)


if __name__ == "__main__":
    main()
