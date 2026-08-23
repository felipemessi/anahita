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
    ClassLevelFeature,
    Item,
    Race,
    RaceAbilityBonus,
    RaceI18n,
    RaceTrait,
    RaceTraitI18n,
    Spell,
    SubclassDefinition,
    Subrace,
    SubraceI18n,
    SubraceTrait,
    SubraceTraitI18n,
    WeaponDetail,
)

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


async def _seed_classes(session: AsyncSession) -> None:
    count = await session.scalar(select(ClassDefinition).limit(1))
    if count is not None:
        return

    data = json.loads((_DATA_DIR / "classes.json").read_text())
    for entry in data:
        cls = ClassDefinition(
            id=uuid.uuid4(),
            name=entry["name"],
            hit_die=entry["hit_die"],
            primary_ability=entry["primary_ability"],
            saving_throw_proficiencies=entry["saving_throw_proficiencies"],
            is_custom=False,
        )
        session.add(cls)

        for feat in entry.get("level_features", []):
            session.add(
                ClassLevelFeature(
                    id=uuid.uuid4(),
                    class_definition_id=cls.id,
                    level=feat["level"],
                    feature_name=feat["feature_name"],
                    description=feat["description"],
                    mechanical_effect=feat.get("mechanical_effect"),
                )
            )

        for sc in entry.get("subclasses", []):
            session.add(
                SubclassDefinition(
                    id=uuid.uuid4(),
                    class_definition_id=cls.id,
                    name=sc["name"],
                    description=sc["description"],
                    is_custom=False,
                )
            )


async def _seed_spells(session: AsyncSession) -> None:
    count = await session.scalar(select(Spell).limit(1))
    if count is not None:
        return

    data = json.loads((_DATA_DIR / "spells.json").read_text())
    for entry in data:
        session.add(
            Spell(
                id=uuid.uuid4(),
                name=entry["name"],
                level=entry["level"],
                school=entry["school"],
                casting_time=entry["casting_time"],
                range=entry["range"],
                duration=entry["duration"],
                components=entry["components"],
                ritual=entry["ritual"],
                concentration=entry["concentration"],
                description=entry["description"],
                higher_levels=entry.get("higher_levels"),
            )
        )


async def _seed_items(session: AsyncSession) -> None:
    count = await session.scalar(select(Item).limit(1))
    if count is not None:
        return

    data = json.loads((_DATA_DIR / "items.json").read_text())
    for entry in data:
        item = Item(
            id=uuid.uuid4(),
            name=entry["name"],
            item_type=entry["item_type"],
            rarity=entry.get("rarity"),
            weight=entry["weight"],
            cost=entry["cost"],
            description=entry["description"],
            properties=entry.get("properties"),
        )
        session.add(item)

        if wd := entry.get("weapon_detail"):
            session.add(
                WeaponDetail(
                    id=uuid.uuid4(),
                    item_id=item.id,
                    damage_dice=wd["damage_dice"],
                    damage_type=wd["damage_type"],
                    weapon_range=wd["weapon_range"],
                    weapon_properties=wd.get("weapon_properties"),
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
