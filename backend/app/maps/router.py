"""HTTP router for the maps domain."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Form, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.core.dependencies import get_current_user
from app.database import get_db
from app.maps.schemas import (
    MapTokenCreate,
    MapTokenMove,
    MapTokenRead,
    SessionMapRead,
)
from app.maps.service import MapService
from app.storage import get_storage_service
from app.storage.base import StorageService

router = APIRouter(tags=["maps"])

DB = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


def get_map_service(
    storage: Annotated[StorageService, Depends(get_storage_service)],
) -> MapService:
    """Return a MapService wired to the configured StorageService."""
    return MapService(storage)


MapSvc = Annotated[MapService, Depends(get_map_service)]


@router.post(
    "/sessions/{session_id}/maps",
    response_model=SessionMapRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_map(
    session_id: uuid.UUID,
    user: CurrentUser,
    db: DB,
    service: MapSvc,
    name: Annotated[str, Form()],
    width_px: Annotated[int, Form()],
    height_px: Annotated[int, Form()],
    grid_size_px: Annotated[int, Form()],
    file: UploadFile,
) -> SessionMapRead:
    """Upload a battle map image for a session, with its grid geometry. DM only."""
    file_bytes = await file.read()
    return await service.create_map(
        session_id,
        user.id,
        name=name,
        file_bytes=file_bytes,
        file_name=file.filename,
        content_type=file.content_type,
        width_px=width_px,
        height_px=height_px,
        grid_size_px=grid_size_px,
        db=db,
    )


@router.get("/sessions/{session_id}/maps", response_model=list[SessionMapRead])
async def list_maps(
    session_id: uuid.UUID,
    user: CurrentUser,
    db: DB,
    service: MapSvc,
) -> list[SessionMapRead]:
    """List a session's maps. Viewable by any campaign member."""
    return await service.list_maps(session_id, user.id, db)


@router.get("/maps/{map_id}/tokens/in-radius", response_model=list[MapTokenRead])
async def tokens_in_radius(
    map_id: uuid.UUID,
    center_x: int,
    center_y: int,
    radius_cells: int,
    user: CurrentUser,
    db: DB,
    service: MapSvc,
) -> list[MapTokenRead]:
    """List tokens within `radius_cells` of a cell — area target selection."""
    return await service.tokens_in_radius(
        map_id,
        user.id,
        center_x=center_x,
        center_y=center_y,
        radius_cells=radius_cells,
        db=db,
    )


@router.post(
    "/maps/{map_id}/tokens",
    response_model=MapTokenRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_token(
    map_id: uuid.UUID,
    body: MapTokenCreate,
    user: CurrentUser,
    db: DB,
    service: MapSvc,
) -> MapTokenRead:
    """Place a token (PC/NPC/monster/manual) on a map. DM only."""
    return await service.create_token(map_id, user.id, body, db)


@router.patch("/tokens/{token_id}", response_model=MapTokenRead)
async def move_token(
    token_id: uuid.UUID,
    body: MapTokenMove,
    user: CurrentUser,
    db: DB,
    service: MapSvc,
) -> MapTokenRead:
    """Reposition a token. DM may move any; a player only their own (speed-limited)."""
    return await service.update_token_position(token_id, user.id, body.x, body.y, db)


@router.delete("/tokens/{token_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_token(
    token_id: uuid.UUID,
    user: CurrentUser,
    db: DB,
    service: MapSvc,
) -> None:
    """Remove a token from a map. DM only."""
    await service.delete_token(token_id, user.id, db)
