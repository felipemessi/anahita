"""Integration tests for WikiService using SQLite in-memory database."""

import uuid

import pytest
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.campaigns.domain import CampaignRole
from app.campaigns.models import Campaign, CampaignMember
from app.wiki.models import WikiPageLink
from app.wiki.schemas import WikiPageCreate, WikiPageLinkCreate, WikiPageUpdate
from app.wiki.service import WikiService
from app.world.models import NPC, Faction


async def _make_user(db: AsyncSession, *, email: str) -> User:
    user = User(email=email, username=email.split("@")[0], hashed_password="x")
    db.add(user)
    await db.flush()
    return user


async def _make_campaign_with_dm_and_player(
    db: AsyncSession,
) -> tuple[Campaign, User, User]:
    marker = uuid.uuid4().hex[:8]
    dm = await _make_user(db, email=f"dm-{marker}@example.com")
    player = await _make_user(db, email=f"player-{marker}@example.com")
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


async def test_slug_derives_from_title_and_dedupes_on_collision(
    db: AsyncSession,
) -> None:
    """A second page with the same title gets a suffixed, unique slug."""
    campaign, dm, _player = await _make_campaign_with_dm_and_player(db)
    service = WikiService()

    first = await service.create_page(
        campaign.id, dm.id, WikiPageCreate(title="The Sunken Temple"), db
    )
    second = await service.create_page(
        campaign.id, dm.id, WikiPageCreate(title="The Sunken Temple"), db
    )

    assert first.slug == "the-sunken-temple"
    assert second.slug == "the-sunken-temple-2"


async def test_player_cannot_create_page(db: AsyncSession) -> None:
    """A non-DM member cannot create a wiki page."""
    campaign, _dm, player = await _make_campaign_with_dm_and_player(db)
    service = WikiService()

    with pytest.raises(HTTPException) as exc:
        await service.create_page(campaign.id, player.id, WikiPageCreate(title="X"), db)
    assert exc.value.status_code == 403


async def test_player_can_read_pages(db: AsyncSession) -> None:
    """A player (non-DM member) can list and read pages."""
    campaign, dm, player = await _make_campaign_with_dm_and_player(db)
    service = WikiService()
    page = await service.create_page(
        campaign.id, dm.id, WikiPageCreate(title="Lore", content="Once upon a time"), db
    )

    pages = await service.list_pages(campaign.id, player.id, db)
    assert [p.id for p in pages] == [page.id]

    fetched, links = await service.get_page(page.id, player.id, db)
    assert fetched.content == "Once upon a time"
    assert links == []


async def test_update_title_regenerates_slug(db: AsyncSession) -> None:
    """Changing a page's title regenerates its slug."""
    campaign, dm, _player = await _make_campaign_with_dm_and_player(db)
    service = WikiService()
    page = await service.create_page(
        campaign.id, dm.id, WikiPageCreate(title="Old Title"), db
    )

    updated = await service.update_page(
        page.id, dm.id, WikiPageUpdate(title="New Title"), db
    )

    assert updated.slug == "new-title"


async def test_link_rejects_more_than_one_target(db: AsyncSession) -> None:
    """A link naming both an NPC and a faction is rejected."""
    campaign, dm, _player = await _make_campaign_with_dm_and_player(db)
    service = WikiService()
    page = await service.create_page(campaign.id, dm.id, WikiPageCreate(title="X"), db)
    npc = NPC(campaign_id=campaign.id, name="Bob", race="Human", description="")
    faction = Faction(campaign_id=campaign.id, name="Guild", description="")
    db.add_all([npc, faction])
    await db.commit()

    with pytest.raises(HTTPException) as exc:
        await service.create_link(
            page.id,
            dm.id,
            WikiPageLinkCreate(npc_id=npc.id, faction_id=faction.id),
            db,
        )
    assert exc.value.status_code == 422


async def test_link_to_npc_from_another_campaign_is_rejected(
    db: AsyncSession,
) -> None:
    """A link cannot point at an NPC belonging to a different campaign."""
    campaign, dm, _player = await _make_campaign_with_dm_and_player(db)
    other_campaign, _other_dm, _other_player = (
        await _make_campaign_with_dm_and_player(db)
    )
    service = WikiService()
    page = await service.create_page(campaign.id, dm.id, WikiPageCreate(title="X"), db)
    foreign_npc = NPC(
        campaign_id=other_campaign.id, name="Stranger", race="Elf", description=""
    )
    db.add(foreign_npc)
    await db.commit()

    with pytest.raises(HTTPException) as exc:
        await service.create_link(
            page.id, dm.id, WikiPageLinkCreate(npc_id=foreign_npc.id), db
        )
    assert exc.value.status_code == 404


async def test_delete_page_cascades_its_links(db: AsyncSession) -> None:
    """Deleting a wiki page also deletes its links."""
    campaign, dm, _player = await _make_campaign_with_dm_and_player(db)
    service = WikiService()
    page = await service.create_page(campaign.id, dm.id, WikiPageCreate(title="X"), db)
    npc = NPC(campaign_id=campaign.id, name="Bob", race="Human", description="")
    db.add(npc)
    await db.commit()
    await service.create_link(page.id, dm.id, WikiPageLinkCreate(npc_id=npc.id), db)

    await service.delete_page(page.id, dm.id, db)

    remaining = await db.execute(
        select(WikiPageLink).where(WikiPageLink.wiki_page_id == page.id)
    )
    assert remaining.scalars().all() == []
