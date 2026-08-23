"""Tests for the generic `get_translated` i18n fallback helper."""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.catalog import service
from app.catalog.models import Condition, ConditionI18n


@pytest.mark.asyncio
async def test_get_translated_falls_back_to_en_when_locale_missing(
    db: AsyncSession,
) -> None:
    """When the active locale has no `_i18n` row, fall back to `en`."""
    condition = Condition(id=uuid.uuid4(), index="blinded", is_custom=False)
    db.add(condition)
    db.add(
        ConditionI18n(
            id=uuid.uuid4(),
            entity_id=condition.id,
            locale="en",
            name="Blinded",
            desc="A blinded creature can't see.",
        )
    )
    await db.commit()

    translated = await service.get_translated(
        db,
        ConditionI18n,
        ConditionI18n.entity_id,
        entity_id=condition.id,
        locale="pt-BR",
    )

    assert translated is not None
    assert translated.locale == "en"
    assert translated.name == "Blinded"


@pytest.mark.asyncio
async def test_get_translated_uses_specific_locale_when_present(
    db: AsyncSession,
) -> None:
    """When the active locale has an `_i18n` row, use it instead of `en`."""
    condition = Condition(id=uuid.uuid4(), index="blinded", is_custom=False)
    db.add(condition)
    db.add(
        ConditionI18n(
            id=uuid.uuid4(),
            entity_id=condition.id,
            locale="en",
            name="Blinded",
            desc="A blinded creature can't see.",
        )
    )
    db.add(
        ConditionI18n(
            id=uuid.uuid4(),
            entity_id=condition.id,
            locale="pt-BR",
            name="Cego",
            desc="Uma criatura cega não pode ver.",
        )
    )
    await db.commit()

    translated = await service.get_translated(
        db,
        ConditionI18n,
        ConditionI18n.entity_id,
        entity_id=condition.id,
        locale="pt-BR",
    )

    assert translated is not None
    assert translated.locale == "pt-BR"
    assert translated.name == "Cego"


@pytest.mark.asyncio
async def test_get_translated_returns_none_when_no_translation_exists(
    db: AsyncSession,
) -> None:
    """When neither the locale nor `en` has a row, return None."""
    condition = Condition(id=uuid.uuid4(), index="prone", is_custom=False)
    db.add(condition)
    await db.commit()

    translated = await service.get_translated(
        db,
        ConditionI18n,
        ConditionI18n.entity_id,
        entity_id=condition.id,
        locale="pt-BR",
    )

    assert translated is None
