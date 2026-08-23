"""Tests for the `is_custom`/`campaign_id` invariant shared by every catalog entity."""

import uuid

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.catalog import service
from app.catalog.domain import CustomCampaignScopeError, validate_custom_campaign_scope
from app.catalog.models import Race


def test_validate_rejects_custom_without_campaign() -> None:
    """`is_custom=True` requires a `campaign_id`."""
    with pytest.raises(CustomCampaignScopeError):
        validate_custom_campaign_scope(is_custom=True, campaign_id=None)


def test_validate_rejects_non_custom_with_campaign() -> None:
    """`is_custom=False` must not carry a `campaign_id`."""
    with pytest.raises(CustomCampaignScopeError):
        validate_custom_campaign_scope(is_custom=False, campaign_id=uuid.uuid4())


def test_validate_accepts_srd_content() -> None:
    """SRD content (`is_custom=False`, `campaign_id=None`) is valid."""
    validate_custom_campaign_scope(is_custom=False, campaign_id=None)


def test_validate_accepts_homebrew_content() -> None:
    """Homebrew content (`is_custom=True`, `campaign_id` set) is valid."""
    validate_custom_campaign_scope(is_custom=True, campaign_id=uuid.uuid4())


@pytest.mark.asyncio
async def test_db_check_constraint_rejects_custom_without_campaign(
    db: AsyncSession,
) -> None:
    """The CHECK constraint mirrors the Python-level invariant at the DB level."""
    db.add(
        Race(
            id=uuid.uuid4(),
            name="Broken Homebrew Race",
            speed=30,
            is_custom=True,
            campaign_id=None,
        )
    )
    with pytest.raises(IntegrityError):
        await db.commit()


@pytest.mark.asyncio
async def test_list_races_scoped_to_campaign_includes_srd_and_own_homebrew(
    db: AsyncSession,
) -> None:
    """`list_races(campaign_id=X)` returns SRD + own campaign homebrew, not others'."""
    campaign_a = uuid.uuid4()
    campaign_b = uuid.uuid4()

    srd_race = Race(id=uuid.uuid4(), name="Human", speed=30, is_custom=False)
    homebrew_a = Race(
        id=uuid.uuid4(),
        name="Homebrew A",
        speed=30,
        is_custom=True,
        campaign_id=campaign_a,
    )
    homebrew_b = Race(
        id=uuid.uuid4(),
        name="Homebrew B",
        speed=30,
        is_custom=True,
        campaign_id=campaign_b,
    )
    db.add_all([srd_race, homebrew_a, homebrew_b])
    await db.commit()

    results = await service.list_races(db, campaign_id=campaign_a)
    names = {r.name for r in results}

    assert names == {"Human", "Homebrew A"}
