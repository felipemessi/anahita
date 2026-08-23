"""Integration tests for WorldService using SQLite in-memory database."""

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.campaigns.domain import CampaignRole
from app.campaigns.models import Campaign, CampaignMember
from app.catalog.models import Monster
from app.sessions.models import Session
from app.world.schemas import (
    FactionCreate,
    FactionRelationshipCreate,
    LocationCreate,
    LocationParentUpdate,
    LocationSessionCreate,
    NPCCreate,
    NPCFactionCreate,
    NPCLocationCreate,
    NPCSessionCreate,
)
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


async def test_location_tree_resolves_three_levels(db: AsyncSession) -> None:
    """A region → city → tavern chain resolves as a nested tree."""
    campaign, dm, _player = await _make_campaign_with_dm_and_player(db)
    service = WorldService()

    region = await service.create_location(
        campaign.id,
        dm.id,
        LocationCreate(name="Sword Coast", location_type="region"),
        db,
    )
    city = await service.create_location(
        campaign.id,
        dm.id,
        LocationCreate(
            name="Waterdeep", location_type="city", parent_location_id=region.id
        ),
        db,
    )
    tavern = await service.create_location(
        campaign.id,
        dm.id,
        LocationCreate(
            name="Yawning Portal", location_type="building", parent_location_id=city.id
        ),
        db,
    )

    tree = await service.get_location_tree(campaign.id, dm.id, db)

    assert [node.id for node in tree] == [region.id]
    assert [node.id for node in tree[0].children] == [city.id]
    assert [node.id for node in tree[0].children[0].children] == [tavern.id]


async def test_reparenting_location_into_its_own_descendant_is_rejected(
    db: AsyncSession,
) -> None:
    """Setting a location's parent to one of its own descendants is a cycle."""
    campaign, dm, _player = await _make_campaign_with_dm_and_player(db)
    service = WorldService()

    region = await service.create_location(
        campaign.id,
        dm.id,
        LocationCreate(name="Sword Coast", location_type="region"),
        db,
    )
    city = await service.create_location(
        campaign.id,
        dm.id,
        LocationCreate(
            name="Waterdeep", location_type="city", parent_location_id=region.id
        ),
        db,
    )

    with pytest.raises(HTTPException) as exc:
        await service.update_location_parent(
            region.id, dm.id, LocationParentUpdate(parent_location_id=city.id), db
        )
    assert exc.value.status_code == 400


async def test_reparenting_location_to_itself_is_rejected(db: AsyncSession) -> None:
    """A location cannot be set as its own parent."""
    campaign, dm, _player = await _make_campaign_with_dm_and_player(db)
    service = WorldService()

    region = await service.create_location(
        campaign.id,
        dm.id,
        LocationCreate(name="Sword Coast", location_type="region"),
        db,
    )

    with pytest.raises(HTTPException) as exc:
        await service.update_location_parent(
            region.id, dm.id, LocationParentUpdate(parent_location_id=region.id), db
        )
    assert exc.value.status_code == 400


async def test_dm_can_link_npc_to_faction_with_role(db: AsyncSession) -> None:
    """An NPC-faction link records the NPC's role in the faction."""
    campaign, dm, _player = await _make_campaign_with_dm_and_player(db)
    service = WorldService()
    npc = await service.create_npc(
        campaign.id, dm.id, NPCCreate(name="Volo", race="Human"), db
    )
    faction = await service.create_faction(
        campaign.id, dm.id, FactionCreate(name="Harpers"), db
    )

    link = await service.link_npc_faction(
        npc.id,
        dm.id,
        NPCFactionCreate(faction_id=faction.id, role_in_faction="Spymaster"),
        db,
    )

    links = await service.list_npc_factions(npc.id, dm.id, db)
    assert [link_.id for link_ in links] == [link.id]
    assert link.role_in_faction == "Spymaster"


async def test_dm_cannot_link_npc_to_faction_from_another_campaign(
    db: AsyncSession,
) -> None:
    """An NPC cannot be linked to a faction from a different campaign."""
    campaign, dm, _player = await _make_campaign_with_dm_and_player(db)
    other_dm = await _make_user(db, email="other-dm@example.com")
    other_campaign = Campaign(name="Other Table", owner_id=other_dm.id)
    db.add(other_campaign)
    await db.flush()
    db.add(
        CampaignMember(
            campaign_id=other_campaign.id, user_id=other_dm.id, role=CampaignRole.dm
        )
    )
    await db.commit()
    service = WorldService()
    npc = await service.create_npc(
        campaign.id, dm.id, NPCCreate(name="Volo", race="Human"), db
    )
    other_faction = await service.create_faction(
        other_campaign.id, other_dm.id, FactionCreate(name="Zhentarim"), db
    )

    with pytest.raises(HTTPException) as exc:
        await service.link_npc_faction(
            npc.id, dm.id, NPCFactionCreate(faction_id=other_faction.id), db
        )
    assert exc.value.status_code == 404


async def test_dm_can_link_npc_to_location_with_presence_type(
    db: AsyncSession,
) -> None:
    """An NPC-location link records how the NPC is present there."""
    campaign, dm, _player = await _make_campaign_with_dm_and_player(db)
    service = WorldService()
    npc = await service.create_npc(
        campaign.id, dm.id, NPCCreate(name="Innkeeper Tom", race="Human"), db
    )
    location = await service.create_location(
        campaign.id, dm.id, LocationCreate(name="The Inn", location_type="building"), db
    )

    link = await service.link_npc_location(
        npc.id,
        dm.id,
        NPCLocationCreate(location_id=location.id, presence_type="resides"),
        db,
    )

    links = await service.list_npc_locations(npc.id, dm.id, db)
    assert [link_.id for link_ in links] == [link.id]
    assert link.presence_type == "resides"


async def test_dm_can_link_npc_and_location_to_a_session(db: AsyncSession) -> None:
    """An NPC's appearance and a location's visit can be recorded for a session."""
    campaign, dm, _player = await _make_campaign_with_dm_and_player(db)
    service = WorldService()
    npc = await service.create_npc(
        campaign.id, dm.id, NPCCreate(name="Innkeeper Tom", race="Human"), db
    )
    location = await service.create_location(
        campaign.id, dm.id, LocationCreate(name="The Inn", location_type="building"), db
    )
    game_session = Session(campaign_id=campaign.id, session_number=1, title="Session 1")
    db.add(game_session)
    await db.commit()

    npc_link = await service.link_npc_session(
        npc.id,
        dm.id,
        NPCSessionCreate(session_id=game_session.id, appearance_note="Gave a quest"),
        db,
    )
    location_link = await service.link_location_session(
        location.id,
        dm.id,
        LocationSessionCreate(session_id=game_session.id, visit_note="First stop"),
        db,
    )

    npc_sessions = await service.list_npc_sessions(npc.id, dm.id, db)
    location_sessions = await service.list_location_sessions(location.id, dm.id, db)
    assert [s.id for s in npc_sessions] == [npc_link.id]
    assert [s.id for s in location_sessions] == [location_link.id]


async def test_dm_can_set_faction_relationship(db: AsyncSession) -> None:
    """A relationship can be set between two factions in the same campaign."""
    campaign, dm, _player = await _make_campaign_with_dm_and_player(db)
    service = WorldService()
    harpers = await service.create_faction(
        campaign.id, dm.id, FactionCreate(name="Harpers"), db
    )
    zhentarim = await service.create_faction(
        campaign.id, dm.id, FactionCreate(name="Zhentarim"), db
    )

    relationship = await service.link_faction_relationship(
        harpers.id,
        dm.id,
        FactionRelationshipCreate(
            faction_b_id=zhentarim.id, relationship_type="hostile"
        ),
        db,
    )

    from_a = await service.list_faction_relationships(harpers.id, dm.id, db)
    from_b = await service.list_faction_relationships(zhentarim.id, dm.id, db)
    assert [r.id for r in from_a] == [relationship.id]
    assert [r.id for r in from_b] == [relationship.id]


async def test_faction_cannot_have_relationship_with_itself(
    db: AsyncSession,
) -> None:
    """A faction cannot be related to itself."""
    campaign, dm, _player = await _make_campaign_with_dm_and_player(db)
    service = WorldService()
    harpers = await service.create_faction(
        campaign.id, dm.id, FactionCreate(name="Harpers"), db
    )

    with pytest.raises(HTTPException) as exc:
        await service.link_faction_relationship(
            harpers.id,
            dm.id,
            FactionRelationshipCreate(
                faction_b_id=harpers.id, relationship_type="allied"
            ),
            db,
        )
    assert exc.value.status_code == 400
