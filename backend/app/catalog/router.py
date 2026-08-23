"""HTTP router for the catalog domain — read-only SRD reference endpoints."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.catalog import service
from app.catalog.schemas import (
    ClassDefinitionRead,
    ClassSummary,
    ItemRead,
    ItemSummary,
    RaceRead,
    RaceSummary,
    SpellRead,
    SpellSummary,
)
from app.database import get_db

router = APIRouter(prefix="/catalog", tags=["catalog"])

DB = Annotated[AsyncSession, Depends(get_db)]
SearchQ = Annotated[str | None, Query(description="Filter by name substring")]
IncludeCustomQ = Annotated[bool, Query()]
LocaleQ = Annotated[str, Query(description="Locale for translated text (en, pt-BR)")]


@router.get("/races", response_model=list[RaceSummary])
async def list_races(
    db: DB,
    search: SearchQ = None,
    include_custom: IncludeCustomQ = True,
    locale: LocaleQ = "en",
) -> list[RaceSummary]:
    """List all races, optionally filtered by name."""
    return await service.list_races_translated(
        db, search=search, include_custom=include_custom, locale=locale
    )


@router.get("/races/{race_id}", response_model=RaceRead)
async def get_race(
    race_id: uuid.UUID,
    db: DB,
    locale: LocaleQ = "en",
) -> RaceRead:
    """Get a race by ID with full details (traits, subraces, ability bonuses)."""
    race = await service.get_race_translated(db, race_id, locale=locale)
    if race is None:
        raise HTTPException(status_code=404, detail="Race not found")
    return race


@router.get("/classes", response_model=list[ClassSummary])
async def list_classes(
    db: DB,
    search: SearchQ = None,
    include_custom: IncludeCustomQ = True,
    locale: LocaleQ = "en",
) -> list[ClassSummary]:
    """List all class definitions, optionally filtered by name."""
    return await service.list_classes_translated(
        db, search=search, include_custom=include_custom, locale=locale
    )


@router.get("/classes/{class_id}", response_model=ClassDefinitionRead)
async def get_class(
    class_id: uuid.UUID,
    db: DB,
    locale: LocaleQ = "en",
) -> ClassDefinitionRead:
    """Get a class definition by ID with full progression (levels, features, subclasses)."""  # noqa: E501
    cls = await service.get_class_translated(db, class_id, locale=locale)
    if cls is None:
        raise HTTPException(status_code=404, detail="Class not found")
    return cls


@router.get("/spells", response_model=list[SpellSummary])
async def list_spells(
    db: DB,
    search: SearchQ = None,
    level: Annotated[
        int | None, Query(ge=0, le=9, description="Filter by spell level")
    ] = None,
    school: Annotated[
        str | None, Query(description="Filter by school of magic (index slug)")
    ] = None,
    include_custom: IncludeCustomQ = True,
    locale: LocaleQ = "en",
) -> list[SpellSummary]:
    """List all spells, optionally filtered by name, level, or school."""
    return await service.list_spells_translated(
        db,
        search=search,
        level=level,
        school=school,
        include_custom=include_custom,
        locale=locale,
    )


@router.get("/spells/{spell_id}", response_model=SpellRead)
async def get_spell(
    spell_id: uuid.UUID,
    db: DB,
    locale: LocaleQ = "en",
) -> SpellRead:
    """Get a spell by ID with full description and casting classes."""
    spell = await service.get_spell_translated(db, spell_id, locale=locale)
    if spell is None:
        raise HTTPException(status_code=404, detail="Spell not found")
    return spell


@router.get("/items", response_model=list[ItemSummary])
async def list_items(
    db: DB,
    search: SearchQ = None,
    item_type: Annotated[str | None, Query(description="Filter by item type")] = None,
) -> list[ItemSummary]:
    """List all items, optionally filtered by name or type."""
    items = await service.list_items(db, search=search, item_type=item_type)
    return [ItemSummary.model_validate(i) for i in items]


@router.get("/items/{item_id}", response_model=ItemRead)
async def get_item(
    item_id: uuid.UUID,
    db: DB,
) -> ItemRead:
    """Get an item by ID with full details (weapon/armor stats if applicable)."""
    item = await service.get_item(db, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return ItemRead.model_validate(item)
