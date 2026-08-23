"""HTTP router for the combat domain — encounter/participant CRUD.

Live turn-flow actions (advance turn, damage/heal, add/remove participant
in-session) go over WebSocket — see `app.combat.ws_router`.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.combat.schemas import (
    EncounterCreate,
    EncounterParticipantCreate,
    EncounterParticipantUpdate,
    EncounterRead,
)
from app.combat.service import CombatService
from app.core.dependencies import get_current_user
from app.database import get_db

router = APIRouter(tags=["combat"])

DB = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


def get_combat_service() -> CombatService:
    """Return a CombatService instance."""
    return CombatService()


@router.post(
    "/sessions/{session_id}/encounters",
    response_model=EncounterRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_encounter(
    session_id: uuid.UUID,
    body: EncounterCreate,
    user: CurrentUser,
    db: DB,
    service: Annotated[CombatService, Depends(get_combat_service)],
) -> EncounterRead:
    """Create an encounter for a session; only the campaign's DM may do this."""
    encounter = await service.create_encounter(session_id, user.id, body, db)
    return EncounterRead.model_validate(encounter)


@router.get("/sessions/{session_id}/encounters", response_model=list[EncounterRead])
async def list_encounters(
    session_id: uuid.UUID,
    user: CurrentUser,
    db: DB,
    service: Annotated[CombatService, Depends(get_combat_service)],
) -> list[EncounterRead]:
    """List a session's encounters. Viewable by any campaign member."""
    encounters = await service.list_encounters(session_id, user.id, db)
    return [EncounterRead.model_validate(e) for e in encounters]


@router.get("/encounters/{encounter_id}", response_model=EncounterRead)
async def get_encounter(
    encounter_id: uuid.UUID,
    user: CurrentUser,
    db: DB,
    service: Annotated[CombatService, Depends(get_combat_service)],
) -> EncounterRead:
    """Get an encounter's detail, with its participants. Viewable by any member."""
    encounter = await service.get_encounter(encounter_id, user.id, db)
    return EncounterRead.model_validate(encounter)


@router.post("/encounters/{encounter_id}/start", response_model=EncounterRead)
async def start_encounter(
    encounter_id: uuid.UUID,
    user: CurrentUser,
    db: DB,
    service: Annotated[CombatService, Depends(get_combat_service)],
) -> EncounterRead:
    """Start a preparing encounter (transitions to `active`). DM only."""
    encounter = await service.start_encounter(encounter_id, user.id, db)
    return EncounterRead.model_validate(encounter)


@router.post(
    "/encounters/{encounter_id}/participants", response_model=EncounterRead
)
async def add_participant(
    encounter_id: uuid.UUID,
    body: EncounterParticipantCreate,
    user: CurrentUser,
    db: DB,
    service: Annotated[CombatService, Depends(get_combat_service)],
) -> EncounterRead:
    """Add a participant (PC, NPC, or manual entry) to an encounter. DM only."""
    encounter = await service.add_participant(encounter_id, user.id, body, db)
    return EncounterRead.model_validate(encounter)


@router.patch(
    "/encounters/{encounter_id}/participants/{participant_id}",
    response_model=EncounterRead,
)
async def update_participant(
    encounter_id: uuid.UUID,
    participant_id: uuid.UUID,
    body: EncounterParticipantUpdate,
    user: CurrentUser,
    db: DB,
    service: Annotated[CombatService, Depends(get_combat_service)],
) -> EncounterRead:
    """Update a participant's fields outside the live turn flow. DM only."""
    encounter = await service.update_participant(
        encounter_id, participant_id, user.id, body, db
    )
    return EncounterRead.model_validate(encounter)


@router.delete(
    "/encounters/{encounter_id}/participants/{participant_id}",
    response_model=EncounterRead,
)
async def remove_participant(
    encounter_id: uuid.UUID,
    participant_id: uuid.UUID,
    user: CurrentUser,
    db: DB,
    service: Annotated[CombatService, Depends(get_combat_service)],
) -> EncounterRead:
    """Remove a participant from an encounter. DM only."""
    encounter = await service.remove_participant(
        encounter_id, participant_id, user.id, db
    )
    return EncounterRead.model_validate(encounter)
