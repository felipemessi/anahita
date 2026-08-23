"""Integration tests for CampaignService using SQLite in-memory database."""

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.campaigns.domain import CampaignRole
from app.campaigns.models import CampaignMember
from app.campaigns.schemas import CampaignCreate
from app.campaigns.service import CampaignService


async def _make_user(db: AsyncSession, *, email: str = "gm@example.com") -> User:
    user = User(email=email, username=email.split("@")[0], hashed_password="x")
    db.add(user)
    await db.flush()
    return user


async def test_create_campaign_sets_owner(db: AsyncSession) -> None:
    """Creating a campaign stores the requested fields and the owner."""
    owner = await _make_user(db)
    service = CampaignService()
    campaign = await service.create_campaign(
        owner.id,
        CampaignCreate(
            name="Curse of Strahd", description="Gothic horror", setting="Barovia"
        ),
        db,
    )
    assert campaign.name == "Curse of Strahd"
    assert campaign.description == "Gothic horror"
    assert campaign.setting == "Barovia"
    assert campaign.owner_id == owner.id


async def test_create_campaign_makes_owner_dm(db: AsyncSession) -> None:
    """Creating a campaign automatically enrolls the owner as its DM."""
    owner = await _make_user(db)
    service = CampaignService()
    campaign = await service.create_campaign(
        owner.id, CampaignCreate(name="Icewind Dale"), db
    )

    result = await db.execute(
        select(CampaignMember).where(CampaignMember.campaign_id == campaign.id)
    )
    members = result.scalars().all()
    assert len(members) == 1
    assert members[0].user_id == owner.id
    assert members[0].role == CampaignRole.dm


async def test_duplicate_membership_violates_unique_constraint(
    db: AsyncSession,
) -> None:
    """A second (campaign_id, user_id) row must be rejected by the DB constraint."""
    owner = await _make_user(db)
    service = CampaignService()
    campaign = await service.create_campaign(
        owner.id, CampaignCreate(name="Dragon Heist"), db
    )

    db.add(
        CampaignMember(
            campaign_id=campaign.id, user_id=owner.id, role=CampaignRole.player
        )
    )
    with pytest.raises(IntegrityError):
        await db.flush()
