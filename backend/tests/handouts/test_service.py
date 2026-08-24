"""Integration tests for HandoutService using SQLite in-memory database."""

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.handouts.schemas import HandoutCreate
from app.handouts.service import HandoutService
from tests.handouts.conftest import FakeStorageService


async def test_dm_creates_handout_with_file(
    db: AsyncSession, campaign_with_session
) -> None:
    """The DM can create a handout with an uploaded file, resolved to a URL."""
    storage = FakeStorageService()
    service = HandoutService(storage)

    handout = await service.create_handout(
        campaign_with_session.campaign_id,
        campaign_with_session.dm_id,
        HandoutCreate(title="Old Map", handout_type="map"),
        db,
        file_bytes=b"binary-map-data",
        file_name="map.png",
        content_type="image/png",
    )

    assert handout.title == "Old Map"
    assert handout.is_revealed is False
    assert handout.url is not None
    assert storage.files  # the file was actually persisted


async def test_player_cannot_create_handout(
    db: AsyncSession, campaign_with_session
) -> None:
    """A non-DM member is rejected when creating a handout."""
    service = HandoutService(FakeStorageService())

    with pytest.raises(HTTPException) as exc_info:
        await service.create_handout(
            campaign_with_session.campaign_id,
            campaign_with_session.player_id,
            HandoutCreate(title="Secret", handout_type="text", content="shh"),
            db,
            file_bytes=None,
            file_name=None,
            content_type=None,
        )
    assert exc_info.value.status_code == 403


async def test_dm_sees_all_handouts_player_sees_only_revealed(
    db: AsyncSession, campaign_with_session
) -> None:
    """DM sees every handout; a player only sees the revealed ones."""
    service = HandoutService(FakeStorageService())
    await service.create_handout(
        campaign_with_session.campaign_id,
        campaign_with_session.dm_id,
        HandoutCreate(title="Hidden note", handout_type="text", content="shh"),
        db,
        file_bytes=None,
        file_name=None,
        content_type=None,
    )
    revealed = await service.create_handout(
        campaign_with_session.campaign_id,
        campaign_with_session.dm_id,
        HandoutCreate(title="Public note", handout_type="text", content="hi"),
        db,
        file_bytes=None,
        file_name=None,
        content_type=None,
    )
    await service.reveal_handout(revealed.id, campaign_with_session.dm_id, db)

    dm_view = await service.list_handouts(
        campaign_with_session.campaign_id, campaign_with_session.dm_id, db
    )
    player_view = await service.list_handouts(
        campaign_with_session.campaign_id, campaign_with_session.player_id, db
    )

    assert {h.title for h in dm_view} == {"Hidden note", "Public note"}
    assert {h.title for h in player_view} == {"Public note"}


async def test_player_cannot_get_unrevealed_handout(
    db: AsyncSession, campaign_with_session
) -> None:
    """GET on an unrevealed handout 404s for a player, even by direct id."""
    service = HandoutService(FakeStorageService())
    handout = await service.create_handout(
        campaign_with_session.campaign_id,
        campaign_with_session.dm_id,
        HandoutCreate(title="Hidden note", handout_type="text", content="shh"),
        db,
        file_bytes=None,
        file_name=None,
        content_type=None,
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.get_handout(handout.id, campaign_with_session.player_id, db)
    assert exc_info.value.status_code == 404


async def test_reveal_sets_revealed_flag_and_timestamp(
    db: AsyncSession, campaign_with_session
) -> None:
    """Revealing a handout sets is_revealed and stamps revealed_at."""
    service = HandoutService(FakeStorageService())
    handout = await service.create_handout(
        campaign_with_session.campaign_id,
        campaign_with_session.dm_id,
        HandoutCreate(title="Note", handout_type="text", content="hi"),
        db,
        file_bytes=None,
        file_name=None,
        content_type=None,
    )

    revealed = await service.reveal_handout(handout.id, campaign_with_session.dm_id, db)

    assert revealed.is_revealed is True
    assert revealed.revealed_at is not None
