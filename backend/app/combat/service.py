"""CombatService orchestrates encounter and participant management.

Covers both the REST CRUD that happens outside the live turn flow
(creating/listing encounters, starting one, adding/updating/removing
participants) and the live actions driven by `app.combat.ws_router` over
WebSocket (advance turn, damage/heal/condition, end encounter) — the two
share the same permission rules and read-model, so one service backs both.
"""

import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.campaigns.domain import CampaignRole
from app.campaigns.models import CampaignMember
from app.combat.domain import (
    ConditionType,
    EncounterStatus,
    ParticipantKindError,
    TurnAdvanceResult,
    TurnParticipant,
    validate_participant_kind,
)
from app.combat.domain import advance_turn as compute_next_turn
from app.combat.models import Encounter, EncounterCondition, EncounterParticipant
from app.combat.schemas import (
    EncounterCreate,
    EncounterParticipantCreate,
    EncounterParticipantUpdate,
)
from app.sessions.models import Session

_ENCOUNTER_LOAD_OPTIONS = (
    selectinload(Encounter.participants).selectinload(EncounterParticipant.conditions),
)


class CombatService:
    """Orchestrates encounter creation, participant management, and reads."""

    async def create_encounter(
        self,
        session_id: uuid.UUID,
        requester_id: uuid.UUID,
        data: EncounterCreate,
        db: AsyncSession,
    ) -> Encounter:
        """Create an encounter for a session; only the campaign's DM may do this."""
        session = await self._require_dm_for_session(session_id, requester_id, db)

        encounter = Encounter(session_id=session.id, name=data.name)
        db.add(encounter)
        await db.commit()
        return await self._reload_encounter(encounter.id, db)

    async def start_encounter(
        self, encounter_id: uuid.UUID, requester_id: uuid.UUID, db: AsyncSession
    ) -> Encounter:
        """Transition an encounter from `preparing` to `active`. DM only."""
        encounter = await self._load_encounter_or_404(encounter_id, db)
        await self._require_dm_for_session(encounter.session_id, requester_id, db)

        if encounter.status != EncounterStatus.preparing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Only a preparing encounter can be started",
            )
        encounter.status = EncounterStatus.active
        encounter.current_round = 1
        await db.commit()
        return await self._reload_encounter(encounter.id, db)

    async def list_encounters(
        self, session_id: uuid.UUID, requester_id: uuid.UUID, db: AsyncSession
    ) -> list[Encounter]:
        """List a session's encounters. Viewable by any campaign member."""
        session = await self._require_session(session_id, db)
        await self._require_membership(session.campaign_id, requester_id, db)

        result = await db.execute(
            select(Encounter)
            .where(Encounter.session_id == session_id)
            .options(*_ENCOUNTER_LOAD_OPTIONS)
            .order_by(Encounter.created_at)
        )
        return list(result.scalars().all())

    async def get_encounter(
        self, encounter_id: uuid.UUID, requester_id: uuid.UUID, db: AsyncSession
    ) -> Encounter:
        """Get an encounter's detail. Viewable by any campaign member."""
        encounter, _member = await self.get_encounter_membership(
            encounter_id, requester_id, db
        )
        return encounter

    async def get_encounter_membership(
        self, encounter_id: uuid.UUID, requester_id: uuid.UUID, db: AsyncSession
    ) -> tuple[Encounter, CampaignMember]:
        """Load an encounter plus the requester's membership in its campaign.

        Reused by the WebSocket handler to authenticate a connection and
        learn the requester's role (DM vs. player) in one call.
        """
        encounter = await self._load_encounter_or_404(encounter_id, db)
        session = await self._require_session(encounter.session_id, db)
        member = await self._require_membership(session.campaign_id, requester_id, db)
        return encounter, member

    async def add_participant(
        self,
        encounter_id: uuid.UUID,
        requester_id: uuid.UUID,
        data: EncounterParticipantCreate,
        db: AsyncSession,
    ) -> Encounter:
        """Add a participant (PC, NPC, or manual entry) to an encounter. DM only."""
        encounter = await self._load_encounter_or_404(encounter_id, db)
        await self._require_dm_for_session(encounter.session_id, requester_id, db)

        try:
            validate_participant_kind(
                character_id=data.character_id, npc_id=data.npc_id
            )
        except ParticipantKindError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
            ) from exc

        hit_point_current = (
            data.hit_point_current
            if data.hit_point_current is not None
            else data.hit_point_max
        )
        db.add(
            EncounterParticipant(
                encounter_id=encounter.id,
                character_id=data.character_id,
                npc_id=data.npc_id,
                name=data.name,
                initiative=data.initiative,
                hit_point_max=data.hit_point_max,
                hit_point_current=hit_point_current,
                armor_class=data.armor_class,
                turn_order=data.turn_order,
            )
        )
        await db.commit()
        return await self._reload_encounter(encounter.id, db)

    async def update_participant(
        self,
        encounter_id: uuid.UUID,
        participant_id: uuid.UUID,
        requester_id: uuid.UUID,
        data: EncounterParticipantUpdate,
        db: AsyncSession,
    ) -> Encounter:
        """Update a participant's fields outside the live turn flow. DM only."""
        encounter = await self._load_encounter_or_404(encounter_id, db)
        await self._require_dm_for_session(encounter.session_id, requester_id, db)
        participant = self._find_participant_or_404(encounter, participant_id)

        if data.hit_point_current is not None:
            if data.hit_point_current > participant.hit_point_max:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail="hit_point_current cannot exceed hit_point_max",
                )
            participant.hit_point_current = data.hit_point_current
        if data.temporary_hit_points is not None:
            participant.temporary_hit_points = data.temporary_hit_points
        if data.armor_class is not None:
            participant.armor_class = data.armor_class
        if data.initiative is not None:
            participant.initiative = data.initiative
        if data.turn_order is not None:
            participant.turn_order = data.turn_order
        if data.is_active is not None:
            participant.is_active = data.is_active

        await db.commit()
        return await self._reload_encounter(encounter.id, db)

    async def remove_participant(
        self,
        encounter_id: uuid.UUID,
        participant_id: uuid.UUID,
        requester_id: uuid.UUID,
        db: AsyncSession,
    ) -> Encounter:
        """Remove a participant from an encounter. DM only."""
        encounter = await self._load_encounter_or_404(encounter_id, db)
        await self._require_dm_for_session(encounter.session_id, requester_id, db)
        participant = self._find_participant_or_404(encounter, participant_id)

        await db.delete(participant)
        await db.commit()
        return await self._reload_encounter(encounter.id, db)

    async def advance_turn(
        self, encounter_id: uuid.UUID, requester_id: uuid.UUID, db: AsyncSession
    ) -> tuple[Encounter, TurnAdvanceResult]:
        """Advance to the next active participant's turn (live, WS-driven). DM only."""
        encounter = await self._load_encounter_or_404(encounter_id, db)
        await self._require_dm_for_session(encounter.session_id, requester_id, db)

        turn_participants = [
            TurnParticipant(
                id=p.id, turn_order=p.turn_order, is_active=p.is_active
            )
            for p in encounter.participants
        ]
        result = compute_next_turn(
            turn_participants,
            current_round=encounter.current_round,
            current_turn_order=encounter.current_turn_order,
        )
        encounter.current_round = result.round
        encounter.current_turn_order = result.turn_order
        await db.commit()
        return await self._reload_encounter(encounter.id, db), result

    async def end_encounter(
        self, encounter_id: uuid.UUID, requester_id: uuid.UUID, db: AsyncSession
    ) -> Encounter:
        """End an encounter (live, WS-driven): sets it to `completed`. DM only."""
        encounter = await self._load_encounter_or_404(encounter_id, db)
        await self._require_dm_for_session(encounter.session_id, requester_id, db)

        encounter.status = EncounterStatus.completed
        await db.commit()
        return await self._reload_encounter(encounter.id, db)

    async def live_update_participant(
        self,
        encounter_id: uuid.UUID,
        participant_id: uuid.UUID,
        requester_id: uuid.UUID,
        *,
        hit_point_current: int | None,
        temporary_hit_points: int | None,
        armor_class: int | None,
        add_condition: ConditionType | None,
        remove_condition: ConditionType | None,
        db: AsyncSession,
    ) -> EncounterParticipant:
        """Apply damage/heal/AC/condition changes to a participant (WS-driven). DM only.

        Returns just the updated participant (not the whole encounter) — the
        WS handler broadcasts a `participant_updated` event scoped to it.
        """
        encounter = await self._load_encounter_or_404(encounter_id, db)
        await self._require_dm_for_session(encounter.session_id, requester_id, db)
        participant = self._find_participant_or_404(encounter, participant_id)

        if hit_point_current is not None:
            if hit_point_current > participant.hit_point_max:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail="hit_point_current cannot exceed hit_point_max",
                )
            participant.hit_point_current = hit_point_current
        if temporary_hit_points is not None:
            participant.temporary_hit_points = temporary_hit_points
        if armor_class is not None:
            participant.armor_class = armor_class

        if add_condition is not None:
            already_has = any(
                c.condition == add_condition for c in participant.conditions
            )
            if not already_has:
                db.add(
                    EncounterCondition(
                        participant_id=participant.id,
                        condition=add_condition,
                        applied_at_round=encounter.current_round,
                    )
                )
        if remove_condition is not None:
            for condition in list(participant.conditions):
                if condition.condition == remove_condition:
                    await db.delete(condition)

        await db.commit()
        await self._reload_encounter(encounter.id, db)
        result = await db.execute(
            select(EncounterParticipant)
            .where(EncounterParticipant.id == participant.id)
            .options(selectinload(EncounterParticipant.conditions))
            .execution_options(populate_existing=True)
        )
        return result.scalar_one()

    def _find_participant_or_404(
        self, encounter: Encounter, participant_id: uuid.UUID
    ) -> EncounterParticipant:
        for participant in encounter.participants:
            if participant.id == participant_id:
                return participant
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Participant not found"
        )

    async def _reload_encounter(
        self, encounter_id: uuid.UUID, db: AsyncSession
    ) -> Encounter:
        """Reload an encounter with fresh relationships (see characters' equivalent)."""
        result = await db.execute(
            select(Encounter)
            .where(Encounter.id == encounter_id)
            .options(*_ENCOUNTER_LOAD_OPTIONS)
            .execution_options(populate_existing=True)
        )
        return result.scalar_one()

    async def _load_encounter_or_404(
        self, encounter_id: uuid.UUID, db: AsyncSession
    ) -> Encounter:
        result = await db.execute(
            select(Encounter)
            .where(Encounter.id == encounter_id)
            .options(*_ENCOUNTER_LOAD_OPTIONS)
        )
        encounter = result.scalar_one_or_none()
        if encounter is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Encounter not found"
            )
        return encounter

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

    async def _require_dm_for_session(
        self, session_id: uuid.UUID, requester_id: uuid.UUID, db: AsyncSession
    ) -> Session:
        """Fetch `session_id`, ensuring `requester_id` is its campaign's DM."""
        session = await self._require_session(session_id, db)
        member = await self._require_membership(session.campaign_id, requester_id, db)
        if member.role != CampaignRole.dm:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the campaign's DM can manage encounters",
            )
        return session
