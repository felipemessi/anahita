"""Tests for the cross-domain campaign listing query."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.campaigns.schemas import CampaignCreate, CampaignInviteCreate
from app.campaigns.service import CampaignService
from app.queries.campaign_queries import list_campaigns_for_user


async def _make_user(db: AsyncSession, *, email: str) -> User:
    user = User(email=email, username=email.split("@")[0], hashed_password="x")
    db.add(user)
    await db.flush()
    return user


async def test_list_campaigns_for_user_returns_only_own_campaigns(
    db: AsyncSession,
) -> None:
    """A user sees campaigns they belong to, never another user's campaigns."""
    alice = await _make_user(db, email="alice@example.com")
    bob = await _make_user(db, email="bob@example.com")
    service = CampaignService()

    alice_campaign = await service.create_campaign(
        alice.id, CampaignCreate(name="Alice's Table"), db
    )
    await service.create_campaign(bob.id, CampaignCreate(name="Bob's Table"), db)

    alice_campaigns = await list_campaigns_for_user(alice.id, db)
    assert [c.id for c in alice_campaigns] == [alice_campaign.id]


async def test_list_campaigns_for_user_includes_campaigns_joined_as_player(
    db: AsyncSession,
) -> None:
    """A player who redeemed an invite sees the campaign alongside owned ones."""
    dm = await _make_user(db, email="dm@example.com")
    player = await _make_user(db, email="player@example.com")
    service = CampaignService()

    dm_campaign = await service.create_campaign(
        dm.id, CampaignCreate(name="DM's Table"), db
    )
    invite = await service.create_invite(
        dm_campaign.id, dm.id, CampaignInviteCreate(), db
    )
    await service.redeem_invite(invite.invite_code, player.id, db)

    player_campaigns = await list_campaigns_for_user(player.id, db)
    assert [c.id for c in player_campaigns] == [dm_campaign.id]


async def test_list_campaigns_for_user_empty_when_no_membership(
    db: AsyncSession,
) -> None:
    """A user with no memberships gets an empty list, not an error."""
    lonely = await _make_user(db, email="lonely@example.com")
    assert await list_campaigns_for_user(lonely.id, db) == []
