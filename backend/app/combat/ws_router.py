"""WebSocket endpoint for live combat — turn advancement, damage/heal/condition.

PRD §10: envelope `{"event_type": "...", "payload": {...}}`. Server → clients:
`state_sync`, `turn_advanced`, `participant_updated`, `encounter_status_changed`
(plus an `error` event for rejected/invalid commands, not in the PRD table but
needed to give the DM's client feedback). Client (DM only) → server:
`advance_turn`, `update_participant`, `add_participant`, `remove_participant`,
`end_encounter`.
"""

import uuid
from typing import Annotated, Any

import jwt
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
)
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.campaigns.domain import CampaignRole
from app.combat.schemas import (
    EncounterParticipantCreate,
    EncounterParticipantRead,
    EncounterRead,
    WSRemoveParticipantPayload,
    WSUpdateParticipantPayload,
)
from app.combat.service import CombatService
from app.combat.ws_manager import manager
from app.core.security import decode_token
from app.database import get_db

router = APIRouter(tags=["combat-ws"])

_DM_COMMANDS = frozenset(
    {
        "advance_turn",
        "update_participant",
        "add_participant",
        "remove_participant",
        "end_encounter",
    }
)


async def _authenticate(token: str) -> uuid.UUID | None:
    """Resolve `token` (JWT, PRD §10.1) to a user id, or None if invalid."""
    try:
        payload = decode_token(token)
        raw_id = payload.get("sub")
        if not raw_id or not isinstance(raw_id, str):
            return None
        return uuid.UUID(raw_id)
    except (jwt.InvalidTokenError, ValueError):
        return None


@router.websocket("/ws/combat/{encounter_id}")
async def combat_ws(
    websocket: WebSocket,
    encounter_id: uuid.UUID,
    token: Annotated[str, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Live combat socket: syncs state on connect, then streams DM commands.

    Reconnection (PRD §10.5): every new connection — first or Nth — gets a
    fresh `state_sync` right after joining, so a dropped-and-reconnected
    client always ends up consistent with Postgres, the source of truth.
    """
    await websocket.accept()

    user_id = await _authenticate(token)
    if user_id is None:
        await websocket.close(code=4401, reason="Invalid or missing token")
        return

    service = CombatService()
    try:
        encounter, member = await service.get_encounter_membership(
            encounter_id, user_id, db
        )
    except HTTPException:
        await websocket.close(code=4403, reason="Not a member of this campaign")
        return

    is_dm = member.role == CampaignRole.dm
    manager.connect(encounter_id, websocket)
    try:
        await websocket.send_json(
            _envelope("state_sync", EncounterRead.model_validate(encounter))
        )
        while True:
            message = await websocket.receive_json()
            await _handle_message(
                message, encounter_id, user_id, is_dm, service, db, websocket
            )
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(encounter_id, websocket)


def _envelope(
    event_type: str, model: EncounterRead | EncounterParticipantRead | Any
) -> dict[str, Any]:
    """Build a `{"event_type": ..., "payload": ...}` frame from a schema or dict."""
    if isinstance(model, EncounterRead | EncounterParticipantRead):
        payload = model.model_dump(mode="json")
    else:
        payload = model
    return {"event_type": event_type, "payload": payload}


async def _handle_message(
    message: dict[str, Any],
    encounter_id: uuid.UUID,
    user_id: uuid.UUID,
    is_dm: bool,
    service: CombatService,
    db: Any,
    websocket: WebSocket,
) -> None:
    """Dispatch one incoming command, or send an `error` frame if rejected."""
    event_type = message.get("event_type")
    payload = message.get("payload") or {}

    if event_type not in _DM_COMMANDS:
        await websocket.send_json(
            _envelope("error", {"detail": f"Unknown event_type '{event_type}'"})
        )
        return
    if not is_dm:
        await websocket.send_json(
            _envelope("error", {"detail": "Only the DM can send commands"})
        )
        return

    try:
        if event_type == "advance_turn":
            _, result = await service.advance_turn(encounter_id, user_id, db)
            await manager.broadcast(
                encounter_id,
                _envelope(
                    "turn_advanced",
                    {
                        "round": result.round,
                        "turn_order": result.turn_order,
                        "participant_id": str(result.participant_id)
                        if result.participant_id
                        else None,
                    },
                ),
            )
        elif event_type == "update_participant":
            update_data = WSUpdateParticipantPayload.model_validate(payload)
            participant = await service.live_update_participant(
                encounter_id,
                update_data.participant_id,
                user_id,
                hit_point_current=update_data.hit_point_current,
                temporary_hit_points=update_data.temporary_hit_points,
                armor_class=update_data.armor_class,
                add_condition=update_data.add_condition,
                remove_condition=update_data.remove_condition,
                db=db,
            )
            await manager.broadcast(
                encounter_id,
                _envelope(
                    "participant_updated",
                    EncounterParticipantRead.model_validate(participant),
                ),
            )
        elif event_type == "add_participant":
            add_data = EncounterParticipantCreate.model_validate(payload)
            encounter = await service.add_participant(
                encounter_id, user_id, add_data, db
            )
            await manager.broadcast(
                encounter_id,
                _envelope("state_sync", EncounterRead.model_validate(encounter)),
            )
        elif event_type == "remove_participant":
            remove_data = WSRemoveParticipantPayload.model_validate(payload)
            encounter = await service.remove_participant(
                encounter_id, remove_data.participant_id, user_id, db
            )
            await manager.broadcast(
                encounter_id,
                _envelope("state_sync", EncounterRead.model_validate(encounter)),
            )
        elif event_type == "end_encounter":
            encounter = await service.end_encounter(encounter_id, user_id, db)
            await manager.broadcast(
                encounter_id,
                _envelope(
                    "encounter_status_changed", {"status": encounter.status.value}
                ),
            )
    except ValidationError as exc:
        await websocket.send_json(_envelope("error", {"detail": str(exc)}))
    except HTTPException as exc:
        await websocket.send_json(_envelope("error", {"detail": exc.detail}))
