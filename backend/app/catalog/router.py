"""HTTP router for the catalog domain — SRD reference endpoints + homebrew creation."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.campaigns.domain import CampaignRole
from app.catalog import service
from app.catalog.schemas import (
    AbilityScoreDefinitionRead,
    BackgroundCreate,
    BackgroundRead,
    BackgroundSummary,
    ClassDefinitionCreate,
    ClassDefinitionRead,
    ClassSummary,
    FeatCreate,
    FeatRead,
    FeatSummary,
    FeatureRead,
    ItemCreate,
    ItemRead,
    ItemSummary,
    MagicItemCreate,
    MagicItemRead,
    MagicItemSummary,
    MonsterCreate,
    MonsterRead,
    MonsterSummary,
    RaceCreate,
    RaceRead,
    RaceSummary,
    RuleCreate,
    RuleRead,
    RuleSummary,
    SpellCreate,
    SpellRead,
    SpellSummary,
)
from app.core.dependencies import get_current_user
from app.database import get_db
from app.queries.campaign_queries import get_membership_for_user

router = APIRouter(prefix="/catalog", tags=["catalog"])

DB = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]
SearchQ = Annotated[str | None, Query(description="Filter by name substring")]
IncludeCustomQ = Annotated[bool, Query()]
CampaignIdQ = Annotated[
    uuid.UUID | None,
    Query(description="Scope homebrew to this campaign (SRD is always included)"),
]
LocaleQ = Annotated[str, Query(description="Locale for translated text (en, pt-BR)")]


async def _require_dm(campaign_id: uuid.UUID, user: User, db: AsyncSession) -> None:
    """Raise 403 unless `user` is the DM of `campaign_id`."""
    member = await get_membership_for_user(campaign_id, user.id, db)
    if member is None or member.role != CampaignRole.dm:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the campaign's DM can create homebrew content",
        )


async def _require_dm_for_delete(
    campaign_id: uuid.UUID | None, is_custom: bool, user: User, db: AsyncSession
) -> None:
    """Authorize a homebrew delete request (Fase 11 policy).

    SRD content (`campaign_id is None`) can never be deleted through this
    endpoint (403). Homebrew belonging to a campaign the requester isn't a
    member of returns 404 instead of 403 — the requester never learns
    whether homebrew content exists in a campaign they have no access to.
    A member who isn't that campaign's DM gets 403, same as create.
    """
    if not is_custom or campaign_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="SRD content cannot be deleted",
        )
    member = await get_membership_for_user(campaign_id, user.id, db)
    if member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    if member.role != CampaignRole.dm:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the campaign's DM can delete homebrew content",
        )


@router.get("/races", response_model=list[RaceSummary])
async def list_races(
    db: DB,
    search: SearchQ = None,
    include_custom: IncludeCustomQ = True,
    campaign_id: CampaignIdQ = None,
    locale: LocaleQ = "en",
) -> list[RaceSummary]:
    """List all races, optionally filtered by name."""
    return await service.list_races_translated(
        db,
        search=search,
        include_custom=include_custom,
        campaign_id=campaign_id,
        locale=locale,
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


@router.post("/races", response_model=RaceRead, status_code=status.HTTP_201_CREATED)
async def create_race(body: RaceCreate, user: CurrentUser, db: DB) -> RaceRead:
    """Create a homebrew race, scoped to `body.campaign_id`. DM only."""
    await _require_dm(body.campaign_id, user, db)
    return await service.create_custom_race(db, body)


@router.delete("/races/{race_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_race(race_id: uuid.UUID, user: CurrentUser, db: DB) -> None:
    """Delete a homebrew race. DM only, own campaign, 409 if still referenced."""
    race = await service.get_race(db, race_id)
    if race is None:
        raise HTTPException(status_code=404, detail="Race not found")
    await _require_dm_for_delete(race.campaign_id, race.is_custom, user, db)
    await service.delete_custom_race(db, race)


@router.get("/classes", response_model=list[ClassSummary])
async def list_classes(
    db: DB,
    search: SearchQ = None,
    include_custom: IncludeCustomQ = True,
    campaign_id: CampaignIdQ = None,
    locale: LocaleQ = "en",
) -> list[ClassSummary]:
    """List all class definitions, optionally filtered by name."""
    return await service.list_classes_translated(
        db,
        search=search,
        include_custom=include_custom,
        campaign_id=campaign_id,
        locale=locale,
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


@router.post(
    "/classes", response_model=ClassDefinitionRead, status_code=status.HTTP_201_CREATED
)
async def create_class(
    body: ClassDefinitionCreate, user: CurrentUser, db: DB
) -> ClassDefinitionRead:
    """Create a homebrew class, scoped to `body.campaign_id`. DM only."""
    await _require_dm(body.campaign_id, user, db)
    return await service.create_custom_class(db, body)


@router.delete("/classes/{class_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_class(class_id: uuid.UUID, user: CurrentUser, db: DB) -> None:
    """Delete a homebrew class. DM only, own campaign, 409 if still referenced."""
    class_definition = await service.get_class(db, class_id)
    if class_definition is None:
        raise HTTPException(status_code=404, detail="Class not found")
    await _require_dm_for_delete(
        class_definition.campaign_id, class_definition.is_custom, user, db
    )
    await service.delete_custom_class(db, class_definition)


@router.get("/ability-scores", response_model=list[AbilityScoreDefinitionRead])
async def list_ability_scores(db: DB) -> list[AbilityScoreDefinitionRead]:
    """List the 6 core ability scores (str/dex/con/int/wis/cha).

    No translation needed — `index` is a fixed short code, not display
    text. Lets the client resolve a `Spell.save_ability_score_id` to the
    ability it rolls against (Fase 8: saving-throw spell casting).
    """
    scores = await service.list_ability_scores(db)
    return [AbilityScoreDefinitionRead.model_validate(s) for s in scores]


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
    class_index: Annotated[
        str | None,
        Query(description="Filter by class that can cast it (index slug, e.g. wizard)"),
    ] = None,
    include_custom: IncludeCustomQ = True,
    campaign_id: CampaignIdQ = None,
    locale: LocaleQ = "en",
) -> list[SpellSummary]:
    """List all spells, optionally filtered by name, level, school, or class."""
    return await service.list_spells_translated(
        db,
        search=search,
        level=level,
        school=school,
        class_index=class_index,
        include_custom=include_custom,
        campaign_id=campaign_id,
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


@router.post("/spells", response_model=SpellRead, status_code=status.HTTP_201_CREATED)
async def create_spell(body: SpellCreate, user: CurrentUser, db: DB) -> SpellRead:
    """Create a homebrew spell, scoped to `body.campaign_id`. DM only."""
    await _require_dm(body.campaign_id, user, db)
    return await service.create_custom_spell(db, body)


@router.delete("/spells/{spell_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_spell(spell_id: uuid.UUID, user: CurrentUser, db: DB) -> None:
    """Delete a homebrew spell. DM only, own campaign, 409 if still referenced."""
    spell = await service.get_spell(db, spell_id)
    if spell is None:
        raise HTTPException(status_code=404, detail="Spell not found")
    await _require_dm_for_delete(spell.campaign_id, spell.is_custom, user, db)
    await service.delete_custom_spell(db, spell)


@router.get("/items", response_model=list[ItemSummary])
async def list_items(
    db: DB,
    search: SearchQ = None,
    item_type: Annotated[str | None, Query(description="Filter by item type")] = None,
    include_custom: IncludeCustomQ = True,
    campaign_id: CampaignIdQ = None,
    locale: LocaleQ = "en",
) -> list[ItemSummary]:
    """List all items, optionally filtered by name or type."""
    return await service.list_items_translated(
        db,
        search=search,
        item_type=item_type,
        include_custom=include_custom,
        campaign_id=campaign_id,
        locale=locale,
    )


@router.get("/items/{item_id}", response_model=ItemRead)
async def get_item(
    item_id: uuid.UUID,
    db: DB,
    locale: LocaleQ = "en",
) -> ItemRead:
    """Get an item by ID with full details (weapon/armor stats, properties)."""
    item = await service.get_item_translated(db, item_id, locale=locale)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.post("/items", response_model=ItemRead, status_code=status.HTTP_201_CREATED)
async def create_item(body: ItemCreate, user: CurrentUser, db: DB) -> ItemRead:
    """Create a homebrew item, scoped to `body.campaign_id`. DM only."""
    await _require_dm(body.campaign_id, user, db)
    return await service.create_custom_item(db, body)


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(item_id: uuid.UUID, user: CurrentUser, db: DB) -> None:
    """Delete a homebrew item. DM only, own campaign, 409 if still referenced."""
    item = await service.get_item(db, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    await _require_dm_for_delete(item.campaign_id, item.is_custom, user, db)
    await service.delete_custom_item(db, item)


@router.get("/magic-items", response_model=list[MagicItemSummary])
async def list_magic_items(
    db: DB,
    search: SearchQ = None,
    include_custom: IncludeCustomQ = True,
    campaign_id: CampaignIdQ = None,
    locale: LocaleQ = "en",
) -> list[MagicItemSummary]:
    """List all magic items, optionally filtered by name."""
    return await service.list_magic_items_translated(
        db,
        search=search,
        include_custom=include_custom,
        campaign_id=campaign_id,
        locale=locale,
    )


@router.get("/magic-items/{magic_item_id}", response_model=MagicItemRead)
async def get_magic_item(
    magic_item_id: uuid.UUID,
    db: DB,
    locale: LocaleQ = "en",
) -> MagicItemRead:
    """Get a magic item by ID with full details, including its variants."""
    magic_item = await service.get_magic_item_translated(
        db, magic_item_id, locale=locale
    )
    if magic_item is None:
        raise HTTPException(status_code=404, detail="Magic item not found")
    return magic_item


@router.post(
    "/magic-items", response_model=MagicItemRead, status_code=status.HTTP_201_CREATED
)
async def create_magic_item(
    body: MagicItemCreate, user: CurrentUser, db: DB
) -> MagicItemRead:
    """Create a homebrew magic item, scoped to `body.campaign_id`. DM only."""
    await _require_dm(body.campaign_id, user, db)
    return await service.create_custom_magic_item(db, body)


@router.delete("/magic-items/{magic_item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_magic_item(
    magic_item_id: uuid.UUID, user: CurrentUser, db: DB
) -> None:
    """Delete a homebrew magic item. DM only, own campaign, 409 if still referenced."""
    magic_item = await service.get_magic_item(db, magic_item_id)
    if magic_item is None:
        raise HTTPException(status_code=404, detail="Magic item not found")
    await _require_dm_for_delete(
        magic_item.campaign_id, magic_item.is_custom, user, db
    )
    await service.delete_custom_magic_item(db, magic_item)


@router.get("/backgrounds", response_model=list[BackgroundSummary])
async def list_backgrounds(
    db: DB,
    search: SearchQ = None,
    include_custom: IncludeCustomQ = True,
    campaign_id: CampaignIdQ = None,
    locale: LocaleQ = "en",
) -> list[BackgroundSummary]:
    """List all backgrounds, optionally filtered by name."""
    return await service.list_backgrounds_translated(
        db,
        search=search,
        include_custom=include_custom,
        campaign_id=campaign_id,
        locale=locale,
    )


@router.get("/backgrounds/{background_id}", response_model=BackgroundRead)
async def get_background(
    background_id: uuid.UUID,
    db: DB,
    locale: LocaleQ = "en",
) -> BackgroundRead:
    """Get a background by ID with full details (proficiencies, equipment, feature)."""
    background = await service.get_background_translated(
        db, background_id, locale=locale
    )
    if background is None:
        raise HTTPException(status_code=404, detail="Background not found")
    return background


@router.post(
    "/backgrounds", response_model=BackgroundRead, status_code=status.HTTP_201_CREATED
)
async def create_background(
    body: BackgroundCreate, user: CurrentUser, db: DB
) -> BackgroundRead:
    """Create a homebrew background, scoped to `body.campaign_id`. DM only."""
    await _require_dm(body.campaign_id, user, db)
    return await service.create_custom_background(db, body)


@router.delete("/backgrounds/{background_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_background(
    background_id: uuid.UUID, user: CurrentUser, db: DB
) -> None:
    """Delete a homebrew background. DM only, own campaign.

    No reference check: `Character.background` is free text, not a foreign
    key (see `app.queries.catalog_reference_queries`).
    """
    background = await service.get_background(db, background_id)
    if background is None:
        raise HTTPException(status_code=404, detail="Background not found")
    await _require_dm_for_delete(
        background.campaign_id, background.is_custom, user, db
    )
    await service.delete_custom_background(db, background)


@router.get("/features", response_model=list[FeatureRead])
async def list_features(
    db: DB,
    parent_feature_id: Annotated[
        uuid.UUID | None,
        Query(description="List only the named options under this parent feature"),
    ] = None,
    search: SearchQ = None,
    locale: LocaleQ = "en",
) -> list[FeatureRead]:
    """List features, optionally scoped to the options under one parent feature."""
    return await service.list_features_translated(
        db, parent_feature_id=parent_feature_id, search=search, locale=locale
    )


@router.get("/features/{feature_id}", response_model=FeatureRead)
async def get_feature(
    feature_id: uuid.UUID,
    db: DB,
    locale: LocaleQ = "en",
) -> FeatureRead:
    """Get a feature by ID, translated (e.g. resolving a picked level-up option)."""
    feature = await service.get_feature_translated(db, feature_id, locale=locale)
    if feature is None:
        raise HTTPException(status_code=404, detail="Feature not found")
    return feature


@router.get("/feats", response_model=list[FeatSummary])
async def list_feats(
    db: DB,
    search: SearchQ = None,
    include_custom: IncludeCustomQ = True,
    campaign_id: CampaignIdQ = None,
    locale: LocaleQ = "en",
) -> list[FeatSummary]:
    """List all feats, optionally filtered by name."""
    return await service.list_feats_translated(
        db,
        search=search,
        include_custom=include_custom,
        campaign_id=campaign_id,
        locale=locale,
    )


@router.get("/feats/{feat_id}", response_model=FeatRead)
async def get_feat(
    feat_id: uuid.UUID,
    db: DB,
    locale: LocaleQ = "en",
) -> FeatRead:
    """Get a feat by ID with full details, including ability score prerequisites."""
    feat = await service.get_feat_translated(db, feat_id, locale=locale)
    if feat is None:
        raise HTTPException(status_code=404, detail="Feat not found")
    return feat


@router.post("/feats", response_model=FeatRead, status_code=status.HTTP_201_CREATED)
async def create_feat(body: FeatCreate, user: CurrentUser, db: DB) -> FeatRead:
    """Create a homebrew feat, scoped to `body.campaign_id`. DM only."""
    await _require_dm(body.campaign_id, user, db)
    return await service.create_custom_feat(db, body)


@router.delete("/feats/{feat_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_feat(feat_id: uuid.UUID, user: CurrentUser, db: DB) -> None:
    """Delete a homebrew feat. DM only, own campaign.

    No reference check: nothing outside the catalog references a feat (see
    `app.queries.catalog_reference_queries`).
    """
    feat = await service.get_feat(db, feat_id)
    if feat is None:
        raise HTTPException(status_code=404, detail="Feat not found")
    await _require_dm_for_delete(feat.campaign_id, feat.is_custom, user, db)
    await service.delete_custom_feat(db, feat)


@router.get("/monsters", response_model=list[MonsterSummary])
async def list_monsters(
    db: DB,
    search: SearchQ = None,
    include_custom: IncludeCustomQ = True,
    campaign_id: CampaignIdQ = None,
    locale: LocaleQ = "en",
) -> list[MonsterSummary]:
    """List all monsters, optionally filtered by name."""
    return await service.list_monsters_translated(
        db,
        search=search,
        include_custom=include_custom,
        campaign_id=campaign_id,
        locale=locale,
    )


@router.get("/monsters/{monster_id}", response_model=MonsterRead)
async def get_monster(
    monster_id: uuid.UUID,
    db: DB,
    locale: LocaleQ = "en",
) -> MonsterRead:
    """Get a monster by ID with its full stat block."""
    monster = await service.get_monster_translated(db, monster_id, locale=locale)
    if monster is None:
        raise HTTPException(status_code=404, detail="Monster not found")
    return monster


@router.post(
    "/monsters", response_model=MonsterRead, status_code=status.HTTP_201_CREATED
)
async def create_monster(body: MonsterCreate, user: CurrentUser, db: DB) -> MonsterRead:
    """Create a homebrew monster, scoped to `body.campaign_id`. DM only."""
    await _require_dm(body.campaign_id, user, db)
    return await service.create_custom_monster(db, body)


@router.delete("/monsters/{monster_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_monster(monster_id: uuid.UUID, user: CurrentUser, db: DB) -> None:
    """Delete a homebrew monster. DM only, own campaign, 409 if still referenced."""
    monster = await service.get_monster(db, monster_id)
    if monster is None:
        raise HTTPException(status_code=404, detail="Monster not found")
    await _require_dm_for_delete(monster.campaign_id, monster.is_custom, user, db)
    await service.delete_custom_monster(db, monster)


@router.get("/rules", response_model=list[RuleSummary])
async def list_rules(
    db: DB,
    search: SearchQ = None,
    include_custom: IncludeCustomQ = True,
    campaign_id: CampaignIdQ = None,
    locale: LocaleQ = "en",
) -> list[RuleSummary]:
    """List all rules, optionally filtered by name."""
    return await service.list_rules_translated(
        db,
        search=search,
        include_custom=include_custom,
        campaign_id=campaign_id,
        locale=locale,
    )


@router.get("/rules/{rule_id}", response_model=RuleRead)
async def get_rule(
    rule_id: uuid.UUID,
    db: DB,
    locale: LocaleQ = "en",
) -> RuleRead:
    """Get a rule by ID with full details, including its rule sections."""
    rule = await service.get_rule_translated(db, rule_id, locale=locale)
    if rule is None:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule


@router.post("/rules", response_model=RuleRead, status_code=status.HTTP_201_CREATED)
async def create_rule(body: RuleCreate, user: CurrentUser, db: DB) -> RuleRead:
    """Create a homebrew rule, scoped to `body.campaign_id`. DM only."""
    await _require_dm(body.campaign_id, user, db)
    return await service.create_custom_rule(db, body)


@router.delete("/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rule(rule_id: uuid.UUID, user: CurrentUser, db: DB) -> None:
    """Delete a homebrew rule. DM only, own campaign.

    No reference check: nothing outside the catalog references a rule (see
    `app.queries.catalog_reference_queries`).
    """
    rule = await service.get_rule(db, rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="Rule not found")
    await _require_dm_for_delete(rule.campaign_id, rule.is_custom, user, db)
    await service.delete_custom_rule(db, rule)
