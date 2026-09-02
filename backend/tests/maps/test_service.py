"""Integration tests for MapService using SQLite in-memory database."""

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.combat.domain import EncounterStatus
from app.combat.models import Encounter, EncounterParticipant
from app.maps.schemas import MapTokenCreate
from app.maps.service import MapService
from tests.maps.conftest import FakeStorageService


async def _make_map(service: MapService, fx, db: AsyncSession, **overrides):
    defaults = dict(
        name="Old Tavern",
        file_bytes=b"binary-map-data",
        file_name="tavern.png",
        content_type="image/png",
        width_px=1000,
        height_px=800,
        grid_size_px=50,
    )
    defaults.update(overrides)
    return await service.create_map(fx.session_id, fx.dm_id, db=db, **defaults)


async def test_dm_uploads_map(db: AsyncSession, campaign_with_pc) -> None:
    """The DM can upload a map image with grid geometry."""
    storage = FakeStorageService()
    service = MapService(storage)

    session_map = await _make_map(service, campaign_with_pc, db)

    assert session_map.name == "Old Tavern"
    assert session_map.grid_size_px == 50
    assert session_map.url is not None
    assert storage.files


async def test_player_cannot_upload_map(db: AsyncSession, campaign_with_pc) -> None:
    """A non-DM member is rejected (403) when uploading a map."""
    service = MapService(FakeStorageService())

    with pytest.raises(HTTPException) as exc_info:
        await service.create_map(
            campaign_with_pc.session_id,
            campaign_with_pc.player_id,
            name="Sneaky Map",
            file_bytes=b"data",
            file_name="map.png",
            content_type="image/png",
            width_px=100,
            height_px=100,
            grid_size_px=10,
            db=db,
        )
    assert exc_info.value.status_code == 403


async def test_dm_creates_token_for_character(
    db: AsyncSession, campaign_with_pc
) -> None:
    """The DM can place a token linked to a PC on the map."""
    service = MapService(FakeStorageService())
    session_map = await _make_map(service, campaign_with_pc, db)

    token = await service.create_token(
        session_map.id,
        campaign_with_pc.dm_id,
        MapTokenCreate(
            character_id=campaign_with_pc.player_character_id,
            name="Aldric",
            x=2,
            y=3,
        ),
        db,
    )

    assert token.character_id == campaign_with_pc.player_character_id
    assert (token.x, token.y) == (2, 3)


async def test_token_rejects_multiple_kinds(db: AsyncSession, campaign_with_pc) -> None:
    """A token can't reference both a character and a monster."""
    service = MapService(FakeStorageService())
    session_map = await _make_map(service, campaign_with_pc, db)

    with pytest.raises(HTTPException) as exc_info:
        await service.create_token(
            session_map.id,
            campaign_with_pc.dm_id,
            MapTokenCreate(
                character_id=campaign_with_pc.player_character_id,
                monster_id=campaign_with_pc.player_character_id,
                name="Confused",
                x=0,
                y=0,
            ),
            db,
        )
    assert exc_info.value.status_code == 422


async def test_player_moves_own_token_freely_outside_combat(
    db: AsyncSession, campaign_with_pc
) -> None:
    """Outside combat, the owning player can move their token any distance."""
    service = MapService(FakeStorageService())
    session_map = await _make_map(service, campaign_with_pc, db)
    token = await service.create_token(
        session_map.id,
        campaign_with_pc.dm_id,
        MapTokenCreate(
            character_id=campaign_with_pc.player_character_id,
            name="Aldric",
            x=0,
            y=0,
        ),
        db,
    )

    moved = await service.update_token_position(
        token.id, campaign_with_pc.player_id, 50, 50, db
    )

    assert (moved.x, moved.y) == (50, 50)


async def test_player_cannot_move_others_token(
    db: AsyncSession, campaign_with_pc
) -> None:
    """A player can't move a token that isn't linked to their own character."""
    service = MapService(FakeStorageService())
    session_map = await _make_map(service, campaign_with_pc, db)
    token = await service.create_token(
        session_map.id,
        campaign_with_pc.dm_id,
        MapTokenCreate(name="A Goblin", x=0, y=0),
        db,
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.update_token_position(
            token.id, campaign_with_pc.player_id, 1, 1, db
        )
    assert exc_info.value.status_code == 403


async def test_movement_capped_by_speed_on_own_turn_in_active_encounter(
    db: AsyncSession, campaign_with_pc
) -> None:
    """On the character's own turn in an active encounter, movement is speed-capped."""
    service = MapService(FakeStorageService())
    session_map = await _make_map(service, campaign_with_pc, db)
    token = await service.create_token(
        session_map.id,
        campaign_with_pc.dm_id,
        MapTokenCreate(
            character_id=campaign_with_pc.player_character_id,
            name="Aldric",
            x=0,
            y=0,
        ),
        db,
    )

    encounter = Encounter(
        session_id=campaign_with_pc.session_id,
        map_id=session_map.id,
        name="Ambush",
        status=EncounterStatus.active,
        current_round=1,
        current_turn_order=0,
    )
    db.add(encounter)
    await db.flush()
    db.add(
        EncounterParticipant(
            encounter_id=encounter.id,
            character_id=campaign_with_pc.player_character_id,
            name="Aldric",
            initiative=15,
            hit_point_max=10,
            hit_point_current=10,
            armor_class=14,
            turn_order=0,
        )
    )
    await db.commit()

    # Aldric has speed=30 -> 6 cells budget. 7 cells away is rejected.
    with pytest.raises(HTTPException) as exc_info:
        await service.update_token_position(
            token.id, campaign_with_pc.player_id, 7, 0, db
        )
    assert exc_info.value.status_code == 422

    # Exactly at budget succeeds.
    moved = await service.update_token_position(
        token.id, campaign_with_pc.player_id, 6, 0, db
    )
    assert (moved.x, moved.y) == (6, 0)


async def test_dm_moves_any_token_even_on_someone_elses_turn(
    db: AsyncSession, campaign_with_pc
) -> None:
    """The DM can move any token, unconstrained, at any time."""
    service = MapService(FakeStorageService())
    session_map = await _make_map(service, campaign_with_pc, db)
    token = await service.create_token(
        session_map.id,
        campaign_with_pc.dm_id,
        MapTokenCreate(
            character_id=campaign_with_pc.player_character_id,
            name="Aldric",
            x=0,
            y=0,
        ),
        db,
    )

    encounter = Encounter(
        session_id=campaign_with_pc.session_id,
        map_id=session_map.id,
        name="Ambush",
        status=EncounterStatus.active,
        current_round=1,
        current_turn_order=5,
    )
    db.add(encounter)
    await db.flush()
    db.add(
        EncounterParticipant(
            encounter_id=encounter.id,
            character_id=campaign_with_pc.player_character_id,
            name="Aldric",
            initiative=15,
            hit_point_max=10,
            hit_point_current=10,
            armor_class=14,
            turn_order=0,
        )
    )
    await db.commit()

    moved = await service.update_token_position(
        token.id, campaign_with_pc.dm_id, 99, 99, db
    )
    assert (moved.x, moved.y) == (99, 99)


async def test_tokens_in_radius_filters_by_chebyshev_distance(
    db: AsyncSession, campaign_with_pc
) -> None:
    """`tokens_in_radius` (Fase 15 história 5) returns only tokens within range."""
    service = MapService(FakeStorageService())
    session_map = await _make_map(service, campaign_with_pc, db)
    near = await service.create_token(
        session_map.id,
        campaign_with_pc.dm_id,
        MapTokenCreate(name="Near Goblin", x=2, y=2),
        db,
    )
    await service.create_token(
        session_map.id,
        campaign_with_pc.dm_id,
        MapTokenCreate(name="Far Goblin", x=10, y=10),
        db,
    )

    found = await service.tokens_in_radius(
        session_map.id,
        campaign_with_pc.dm_id,
        center_x=0,
        center_y=0,
        radius_cells=4,
        db=db,
    )

    assert [t.id for t in found] == [near.id]


async def test_dm_deletes_token(db: AsyncSession, campaign_with_pc) -> None:
    """The DM can remove a token from a map."""
    service = MapService(FakeStorageService())
    session_map = await _make_map(service, campaign_with_pc, db)
    token = await service.create_token(
        session_map.id,
        campaign_with_pc.dm_id,
        MapTokenCreate(name="A Goblin", x=0, y=0),
        db,
    )

    await service.delete_token(token.id, campaign_with_pc.dm_id, db)

    with pytest.raises(HTTPException) as exc_info:
        await service.update_token_position(token.id, campaign_with_pc.dm_id, 1, 1, db)
    assert exc_info.value.status_code == 404
