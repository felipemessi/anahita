"""MapService orchestrates session maps and token placement/movement.

Movement (backlog Fase 15 história 3): a token linked to a Character is
free to move any distance, except while the map's linked `Encounter` is
`active` **and** it's that character's own turn — then a single move is
capped at the character's speed, in cells (`app.maps.domain.feet_to_cells`/
`cell_distance`). The DM may always move any token, any distance, at any
time. Each `PATCH /tokens/{id}` call is checked independently against the
full speed budget — this app doesn't track cumulative movement already
spent this turn (no such column exists, mirroring how `declare_action`
doesn't track "actions used this turn" either), a documented
simplification.

Real-time (backlog Fase 15 história 4): every mutation below also
broadcasts a `token_added`/`token_moved`/`token_removed` event to
`app.maps.ws_manager.manager`'s registry for the map — covers both the
`move_token` WS command and the plain REST endpoints (a DM using a REST
form should still update everyone's live view), mirroring how
`app.handouts.service.HandoutService.reveal_handout` broadcasts from a
REST action.
"""

import uuid
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.campaigns.domain import CampaignRole
from app.campaigns.models import CampaignMember
from app.characters.models import Character
from app.combat.domain import EncounterStatus
from app.combat.models import Encounter
from app.maps.domain import (
    MapTokenKindError,
    cell_distance,
    feet_to_cells,
    validate_token_kind,
)
from app.maps.models import MapToken, SessionMap
from app.maps.schemas import (
    MapSnapshotRead,
    MapTokenCreate,
    MapTokenRead,
    SessionMapRead,
)
from app.maps.ws_manager import manager as maps_ws_manager
from app.sessions.models import Session
from app.storage.base import StorageService


class MapService:
    """Orchestrates map upload/listing and token creation/movement/removal."""

    def __init__(self, storage: StorageService) -> None:
        """Store the StorageService used to persist/resolve map images."""
        self._storage = storage

    async def create_map(
        self,
        session_id: uuid.UUID,
        requester_id: uuid.UUID,
        *,
        name: str,
        file_bytes: bytes,
        file_name: str | None,
        content_type: str | None,
        width_px: int,
        height_px: int,
        grid_size_px: int,
        db: AsyncSession,
    ) -> SessionMapRead:
        """Upload a map image for a session, with its grid geometry. DM only."""
        session = await self._require_session(session_id, db)
        await self._require_dm(session.campaign_id, requester_id, db)

        key = f"maps/{session_id}/{uuid.uuid4()}_{file_name or 'map'}"
        storage_key = self._storage.upload(
            key, file_bytes, content_type or "application/octet-stream"
        )
        session_map = SessionMap(
            session_id=session_id,
            name=name,
            storage_key=storage_key,
            width_px=width_px,
            height_px=height_px,
            grid_size_px=grid_size_px,
        )
        db.add(session_map)
        await db.commit()
        await db.refresh(session_map)
        return self._map_to_read(session_map)

    async def list_maps(
        self, session_id: uuid.UUID, requester_id: uuid.UUID, db: AsyncSession
    ) -> list[SessionMapRead]:
        """List a session's maps. Viewable by any campaign member."""
        session = await self._require_session(session_id, db)
        await self._require_membership(session.campaign_id, requester_id, db)

        result = await db.execute(
            select(SessionMap)
            .where(SessionMap.session_id == session_id)
            .order_by(SessionMap.created_at)
        )
        return [self._map_to_read(m) for m in result.scalars().all()]

    async def tokens_in_radius(
        self,
        map_id: uuid.UUID,
        requester_id: uuid.UUID,
        *,
        center_x: int,
        center_y: int,
        radius_cells: int,
        db: AsyncSession,
    ) -> list[MapTokenRead]:
        """Tokens within `radius_cells` of `(center_x, center_y)` (Fase 15 história 5).

        The simple geometric target-selection the backlog asks for: the
        frontend drops an area template (e.g. Fireball's 20ft/4-cell
        radius) centered on a cell and calls this to learn which tokens it
        covers, then maps each returned token's `character_id`/`npc_id`/
        `monster_id` to the matching `EncounterParticipant` to build
        `WSDeclareActionPayload.additional_target_ids` — this app has no
        direct FK between a token and a participant, so that join is the
        caller's job (mirrors how `app.maps` and `app.combat` are
        otherwise decoupled domains). Uses `cell_distance` (Chebyshev), the
        same distance rule movement uses, so an area's shape on the grid is
        consistent with how far a token can walk.
        """
        session_map = await self._load_map_or_404(map_id, db)
        session = await self._require_session(session_map.session_id, db)
        member = await self._require_membership(session.campaign_id, requester_id, db)

        result = await db.execute(
            select(MapToken).where(MapToken.map_id == map_id).order_by(MapToken.id)
        )
        tokens = result.scalars().all()
        if member.role != CampaignRole.dm:
            tokens = [t for t in tokens if t.is_visible]
        in_range = [
            t
            for t in tokens
            if cell_distance(center_x, center_y, t.x, t.y) <= radius_cells
        ]
        return [self._token_to_read(t) for t in in_range]

    async def create_token(
        self,
        map_id: uuid.UUID,
        requester_id: uuid.UUID,
        data: MapTokenCreate,
        db: AsyncSession,
    ) -> MapTokenRead:
        """Place a token (PC/NPC/monster/manual) on a map. DM only."""
        session_map = await self._load_map_or_404(map_id, db)
        session = await self._require_session(session_map.session_id, db)
        await self._require_dm(session.campaign_id, requester_id, db)

        try:
            validate_token_kind(
                character_id=data.character_id,
                npc_id=data.npc_id,
                monster_id=data.monster_id,
            )
        except MapTokenKindError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
            ) from exc

        token = MapToken(
            map_id=map_id,
            character_id=data.character_id,
            npc_id=data.npc_id,
            monster_id=data.monster_id,
            name=data.name,
            x=data.x,
            y=data.y,
            is_visible=data.is_visible,
        )
        db.add(token)
        await db.commit()
        await db.refresh(token)
        read = self._token_to_read(token)
        await self._broadcast(map_id, "token_added", read)
        return read

    async def get_snapshot(
        self, map_id: uuid.UUID, requester_id: uuid.UUID, db: AsyncSession
    ) -> MapSnapshotRead:
        """Return the map plus every token on it — sent as `state_sync` on WS connect.

        A non-DM viewer only sees `is_visible=True` tokens — mirrors how
        `app.world.models.NPC` is hidden from players until the DM reveals
        it.
        """
        session_map = await self._load_map_or_404(map_id, db)
        session = await self._require_session(session_map.session_id, db)
        member = await self._require_membership(session.campaign_id, requester_id, db)

        result = await db.execute(
            select(MapToken).where(MapToken.map_id == map_id).order_by(MapToken.id)
        )
        tokens = result.scalars().all()
        if member.role != CampaignRole.dm:
            tokens = [t for t in tokens if t.is_visible]
        return MapSnapshotRead(
            map=self._map_to_read(session_map),
            tokens=[self._token_to_read(t) for t in tokens],
        )

    async def update_token_position(
        self,
        token_id: uuid.UUID,
        requester_id: uuid.UUID,
        new_x: int,
        new_y: int,
        db: AsyncSession,
    ) -> MapTokenRead:
        """Move a token. The DM may always move any token; a player only their own.

        A player's move is capped at their character's speed while it's
        their own turn in an `active` encounter linked to the map — free
        otherwise (see module docstring).
        """
        token = await self._load_token_or_404(token_id, db)
        session_map = await self._load_map_or_404(token.map_id, db)
        session = await self._require_session(session_map.session_id, db)
        member = await self._require_membership(session.campaign_id, requester_id, db)

        if member.role != CampaignRole.dm:
            character = await self._owned_character_or_403(
                token.character_id, requester_id, db
            )
            await self._enforce_movement_limit(
                session_map, token, character, new_x, new_y, db
            )

        token.x = new_x
        token.y = new_y
        await db.commit()
        await db.refresh(token)
        read = self._token_to_read(token)
        await self._broadcast(token.map_id, "token_moved", read)
        return read

    async def delete_token(
        self, token_id: uuid.UUID, requester_id: uuid.UUID, db: AsyncSession
    ) -> None:
        """Remove a token from a map. DM only."""
        token = await self._load_token_or_404(token_id, db)
        session_map = await self._load_map_or_404(token.map_id, db)
        session = await self._require_session(session_map.session_id, db)
        await self._require_dm(session.campaign_id, requester_id, db)

        map_id, token_id_removed = token.map_id, token.id
        await db.delete(token)
        await db.commit()
        await self._broadcast(map_id, "token_removed", {"id": str(token_id_removed)})

    async def _broadcast(
        self, map_id: uuid.UUID, event_type: str, payload: MapTokenRead | dict[str, Any]
    ) -> None:
        """Send a `{"event_type": ..., "payload": ...}` frame to `map_id`'s sockets."""
        body = (
            payload.model_dump(mode="json")
            if isinstance(payload, MapTokenRead)
            else payload
        )
        await maps_ws_manager.broadcast(
            map_id, {"event_type": event_type, "payload": body}
        )

    async def _enforce_movement_limit(
        self,
        session_map: SessionMap,
        token: MapToken,
        character: Character,
        new_x: int,
        new_y: int,
        db: AsyncSession,
    ) -> None:
        """Raise 422 if the move exceeds `character`'s speed on their own turn."""
        result = await db.execute(
            select(Encounter)
            .where(
                Encounter.map_id == session_map.id,
                Encounter.status == EncounterStatus.active,
            )
            .options(selectinload(Encounter.participants))
        )
        encounter = result.scalars().first()
        if encounter is None:
            return

        participant = next(
            (
                p
                for p in encounter.participants
                if p.character_id == character.id and p.is_active
            ),
            None,
        )
        on_own_turn = (
            participant is not None
            and participant.turn_order == encounter.current_turn_order
        )
        if not on_own_turn:
            return

        budget = feet_to_cells(character.speed)
        distance = cell_distance(token.x, token.y, new_x, new_y)
        if distance > budget:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=(
                    f"Move of {distance} cells exceeds {character.name}'s "
                    f"speed of {budget} cells this turn"
                ),
            )

    async def _owned_character_or_403(
        self,
        character_id: uuid.UUID | None,
        requester_id: uuid.UUID,
        db: AsyncSession,
    ) -> Character:
        """Return the Character behind `character_id` if `requester_id` owns it.

        403 for a token with no character (an NPC/monster/manual token — a
        non-DM player can never move those), a character that doesn't
        exist, or one owned by someone else.
        """
        if character_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only move your own character's token",
            )
        result = await db.execute(select(Character).where(Character.id == character_id))
        character = result.scalar_one_or_none()
        if character is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only move your own character's token",
            )
        member_result = await db.execute(
            select(CampaignMember).where(
                CampaignMember.id == character.campaign_member_id
            )
        )
        member = member_result.scalar_one_or_none()
        if member is None or member.user_id != requester_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only move your own character's token",
            )
        return character

    def _map_to_read(self, session_map: SessionMap) -> SessionMapRead:
        return SessionMapRead(
            id=session_map.id,
            session_id=session_map.session_id,
            name=session_map.name,
            url=self._storage.get_url(session_map.storage_key),
            width_px=session_map.width_px,
            height_px=session_map.height_px,
            grid_size_px=session_map.grid_size_px,
            created_at=session_map.created_at,
        )

    def _token_to_read(self, token: MapToken) -> MapTokenRead:
        return MapTokenRead(
            id=token.id,
            map_id=token.map_id,
            character_id=token.character_id,
            npc_id=token.npc_id,
            monster_id=token.monster_id,
            name=token.name,
            x=token.x,
            y=token.y,
            is_visible=token.is_visible,
        )

    async def _load_map_or_404(self, map_id: uuid.UUID, db: AsyncSession) -> SessionMap:
        result = await db.execute(select(SessionMap).where(SessionMap.id == map_id))
        session_map = result.scalar_one_or_none()
        if session_map is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Map not found"
            )
        return session_map

    async def _load_token_or_404(
        self, token_id: uuid.UUID, db: AsyncSession
    ) -> MapToken:
        result = await db.execute(select(MapToken).where(MapToken.id == token_id))
        token = result.scalar_one_or_none()
        if token is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Token not found"
            )
        return token

    async def _require_session(
        self, session_id: uuid.UUID, db: AsyncSession
    ) -> Session:
        result = await db.execute(select(Session).where(Session.id == session_id))
        session = result.scalar_one_or_none()
        if session is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
            )
        return session

    async def _require_membership(
        self, campaign_id: uuid.UUID, requester_id: uuid.UUID, db: AsyncSession
    ) -> CampaignMember:
        result = await db.execute(
            select(CampaignMember).where(
                CampaignMember.campaign_id == campaign_id,
                CampaignMember.user_id == requester_id,
            )
        )
        member = result.scalar_one_or_none()
        if member is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not a member of this campaign",
            )
        return member

    async def _require_dm(
        self, campaign_id: uuid.UUID, requester_id: uuid.UUID, db: AsyncSession
    ) -> CampaignMember:
        member = await self._require_membership(campaign_id, requester_id, db)
        if member.role != CampaignRole.dm:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the campaign's DM can manage maps",
            )
        return member
