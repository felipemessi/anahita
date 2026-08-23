"""Integration tests for campaign invite generation and redemption."""

from datetime import UTC, datetime, timedelta

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.campaigns.domain import CampaignRole
from app.campaigns.models import Campaign, CampaignInvite, CampaignMember
from app.campaigns.schemas import CampaignCreate, CampaignInviteCreate
from app.campaigns.service import CampaignService


async def _make_user(db: AsyncSession, *, email: str) -> User:
    user = User(email=email, username=email.split("@")[0], hashed_password="x")
    db.add(user)
    await db.flush()
    return user


async def test_dm_can_create_invite(db: AsyncSession) -> None:
    """The campaign's DM can generate an invite code."""
    dm = await _make_user(db, email="dm@example.com")
    service = CampaignService()
    campaign = await service.create_campaign(
        dm.id, CampaignCreate(name="Ravenloft"), db
    )

    invite = await service.create_invite(
        campaign.id, dm.id, CampaignInviteCreate(role=CampaignRole.player), db
    )
    assert invite.campaign_id == campaign.id
    assert invite.invite_code
    assert invite.role == CampaignRole.player
    assert invite.used_by is None


async def test_non_dm_cannot_create_invite(db: AsyncSession) -> None:
    """A user who isn't the campaign's DM is rejected with 403."""
    dm = await _make_user(db, email="dm@example.com")
    outsider = await _make_user(db, email="outsider@example.com")
    service = CampaignService()
    campaign = await service.create_campaign(
        dm.id, CampaignCreate(name="Ravenloft"), db
    )

    with pytest.raises(HTTPException) as exc:
        await service.create_invite(
            campaign.id, outsider.id, CampaignInviteCreate(), db
        )
    assert exc.value.status_code == 403


async def test_redeem_invite_creates_membership_with_invite_role(
    db: AsyncSession,
) -> None:
    """Redeeming a valid invite enrolls the user with the invite's role."""
    dm = await _make_user(db, email="dm@example.com")
    player = await _make_user(db, email="player@example.com")
    service = CampaignService()
    campaign = await service.create_campaign(
        dm.id, CampaignCreate(name="Ravenloft"), db
    )
    invite = await service.create_invite(
        campaign.id, dm.id, CampaignInviteCreate(role=CampaignRole.player), db
    )

    member = await service.redeem_invite(invite.invite_code, player.id, db)
    assert member.campaign_id == campaign.id
    assert member.user_id == player.id
    assert member.role == CampaignRole.player

    await db.refresh(invite)
    assert invite.used_by == player.id


async def test_redeem_unknown_invite_code_raises_404(db: AsyncSession) -> None:
    """Redeeming a nonexistent invite code raises 404."""
    player = await _make_user(db, email="player@example.com")
    service = CampaignService()
    with pytest.raises(HTTPException) as exc:
        await service.redeem_invite("does-not-exist", player.id, db)
    assert exc.value.status_code == 404


async def test_redeem_used_invite_raises_409(db: AsyncSession) -> None:
    """Redeeming an already-used invite raises 409."""
    dm = await _make_user(db, email="dm@example.com")
    player = await _make_user(db, email="player@example.com")
    other = await _make_user(db, email="other@example.com")
    service = CampaignService()
    campaign = await service.create_campaign(
        dm.id, CampaignCreate(name="Ravenloft"), db
    )
    invite = await service.create_invite(campaign.id, dm.id, CampaignInviteCreate(), db)

    await service.redeem_invite(invite.invite_code, player.id, db)
    with pytest.raises(HTTPException) as exc:
        await service.redeem_invite(invite.invite_code, other.id, db)
    assert exc.value.status_code == 409


async def test_redeem_expired_invite_raises_410(db: AsyncSession) -> None:
    """Redeeming an expired invite raises 410."""
    dm = await _make_user(db, email="dm@example.com")
    player = await _make_user(db, email="player@example.com")
    campaign = Campaign(name="Ravenloft", owner_id=dm.id)
    db.add(campaign)
    await db.flush()
    db.add(CampaignMember(campaign_id=campaign.id, user_id=dm.id, role=CampaignRole.dm))
    invite = CampaignInvite(
        campaign_id=campaign.id,
        invite_code="expired-code",
        role=CampaignRole.player,
        expires_at=datetime.now(UTC) - timedelta(hours=1),
    )
    db.add(invite)
    await db.commit()

    service = CampaignService()
    with pytest.raises(HTTPException) as exc:
        await service.redeem_invite("expired-code", player.id, db)
    assert exc.value.status_code == 410
