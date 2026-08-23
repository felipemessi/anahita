"""Integration tests for WorldService using SQLite in-memory database."""

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.campaigns.domain import CampaignRole
from app.campaigns.models import Campaign, CampaignMember
from app.catalog.models import Monster
from app.world.schemas import FactionCreate, LocationCreate, NPCCreate
from app.world.service import WorldService


async def _make_user(db: AsyncSession, *, email: str) -> User:
    user = User(email=email, username=email.split("@")[0], hashed_password="x")
    db.add(user)
    await db.flush()
    return user


async def _make_campaign_with_dm_and_player(
    db: AsyncSession,
) -> tuple[Campaign, User, User]:
    dm = await _make_user(db, email="dm@example.com")
    player = await _make_user(db, email="player@example.com")
    campaign = Campaign(name="Test Table", owner_id=dm.id)
    db.add(campaign)
    await db.flush()
    db.add_all(
        [
            CampaignMember(
                campaign_id=campaign.id, user_id=dm.id, role=CampaignRole.dm
            ),
            CampaignMember(
                campaign_id=campaign.id, user_id=player.id, role=CampaignRole.player
            ),
        ]
    )
    await db.commit()
    return campaign, dm, player


def _make_monster(*, is_custom: bool = False, campaign_id: object = None) -> Monster:
    return Monster(
        size="medium",
        creature_type="humanoid",
        alignment="neutral",
        hit_points=10,
        hit_dice="2d8",
        challenge_rating=0.5,
        xp=100,
        strength=10,
        dexterity=10,
        constitution=10,
        intelligence=10,
        wisdom=10,
        charisma=10,
        is_custom=is_custom,
        campaign_id=campaign_id,
    )


async def test_dm_can_create_npc_without_stat_block(db: AsyncSession) -> None:
    """A DM can create a purely narrative NPC with no stat block."""
    campaign, dm, _player = await _make_campaign_with_dm_and_player(db)
    service = WorldService()

    npc = await service.create_npc(
        campaign.id,
        dm.id,
        NPCCreate(name="Innkeeper Tom", race="Human", description="Runs the inn"),
        db,
    )

    assert npc.stat_block_id is None
    assert npc.is_alive is True


async def test_dm_can_create_npc_with_srd_stat_block(db: AsyncSession) -> None:
    """A DM can attach an SRD (non-custom, campaign-less) monster as a stat block."""
    campaign, dm, _player = await _make_campaign_with_dm_and_player(db)
    monster = _make_monster()
    db.add(monster)
    await db.commit()
    service = WorldService()

    npc = await service.create_npc(
        campaign.id,
        dm.id,
        NPCCreate(name="Goblin Boss", race="Goblin", stat_block_id=monster.id),
        db,
    )

    assert npc.stat_block_id == monster.id


async def test_dm_can_create_npc_with_own_campaign_homebrew_monster(
    db: AsyncSession,
) -> None:
    """A DM can attach a homebrew monster scoped to their own campaign."""
    campaign, dm, _player = await _make_campaign_with_dm_and_player(db)
    monster = _make_monster(is_custom=True, campaign_id=campaign.id)
    db.add(monster)
    await db.commit()
    service = WorldService()

    npc = await service.create_npc(
        campaign.id,
        dm.id,
        NPCCreate(name="Homebrew Horror", race="Aberration", stat_block_id=monster.id),
        db,
    )

    assert npc.stat_block_id == monster.id


async def test_dm_cannot_use_another_campaigns_homebrew_monster(
    db: AsyncSession,
) -> None:
    """A homebrew monster from another campaign cannot be used as a stat block."""
    campaign, dm, _player = await _make_campaign_with_dm_and_player(db)
    other_dm = await _make_user(db, email="other-dm@example.com")
    other_campaign = Campaign(name="Other Table", owner_id=other_dm.id)
    db.add(other_campaign)
    await db.flush()
    monster = _make_monster(is_custom=True, campaign_id=other_campaign.id)
    db.add(monster)
    await db.commit()
    service = WorldService()

    with pytest.raises(HTTPException) as exc:
        await service.create_npc(
            campaign.id,
            dm.id,
            NPCCreate(name="Stolen Stats", race="Aberration", stat_block_id=monster.id),
            db,
        )
    assert exc.value.status_code == 404


async def test_player_cannot_create_npc(db: AsyncSession) -> None:
    """A non-DM member cannot create an NPC."""
    campaign, _dm, player = await _make_campaign_with_dm_and_player(db)
    service = WorldService()

    with pytest.raises(HTTPException) as exc:
        await service.create_npc(
            campaign.id, player.id, NPCCreate(name="Sneaky", race="Human"), db
        )
    assert exc.value.status_code == 403


async def test_dm_can_create_location_and_faction(db: AsyncSession) -> None:
    """A DM can create a location and a faction; both are listed back."""
    campaign, dm, _player = await _make_campaign_with_dm_and_player(db)
    service = WorldService()

    location = await service.create_location(
        campaign.id,
        dm.id,
        LocationCreate(name="Waterdeep", location_type="city", description="A city"),
        db,
    )
    faction = await service.create_faction(
        campaign.id,
        dm.id,
        FactionCreate(name="Harpers", description="Secret network"),
        db,
    )

    locations = await service.list_locations(campaign.id, dm.id, db)
    factions = await service.list_factions(campaign.id, dm.id, db)
    assert [loc.id for loc in locations] == [location.id]
    assert [f.id for f in factions] == [faction.id]
