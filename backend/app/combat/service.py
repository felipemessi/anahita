"""CombatService orchestrates encounter and participant management.

Covers both the REST CRUD that happens outside the live turn flow
(creating/listing encounters, starting one, adding/updating/removing
participants) and the live actions driven by `app.combat.ws_router` over
WebSocket (advance turn, damage/heal/condition, end encounter) — the two
share the same permission rules and read-model, so one service backs both.

Public methods return `EncounterRead`/`EncounterParticipantRead` (not raw
ORM rows) — mirrors `CharacterService`, since a participant's `effects` are
computed from its conditions on every read, never persisted (backlog Fase 2
história 3).
"""

import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.campaigns.domain import CampaignRole
from app.campaigns.models import CampaignMember
from app.characters.models import Character
from app.combat.domain import (
    ActionType,
    ConditionType,
    EncounterStatus,
    ParticipantKindError,
    TurnAdvanceResult,
    TurnParticipant,
    validate_participant_kind,
)
from app.combat.domain import advance_turn as compute_next_turn
from app.combat.models import (
    CombatLog,
    Encounter,
    EncounterCondition,
    EncounterParticipant,
)
from app.combat.schemas import (
    CombatLogRead,
    EncounterConditionRead,
    EncounterCreate,
    EncounterParticipantCreate,
    EncounterParticipantRead,
    EncounterParticipantUpdate,
    EncounterRead,
    MechanicalEffectRead,
)
from app.sessions.models import Session
from engine.conditions import get_condition_effects
from engine.types import Condition as EngineCondition
from engine.types import ConditionType as EngineConditionType

_ENCOUNTER_LOAD_OPTIONS = (
    selectinload(Encounter.participants).selectinload(EncounterParticipant.conditions),
)


def participant_to_read(participant: EncounterParticipant) -> EncounterParticipantRead:
    """Build a participant's read schema, resolving its conditions' effects.

    `engine.conditions.get_condition_effects` has no notion of exhaustion
    *level* beyond what `engine.types.Condition.level` carries; the DB
    doesn't track a severity for conditions (PRD §7.6 has no such column),
    so exhaustion is always resolved at level 1 here.
    """
    engine_conditions = [
        EngineCondition(condition_type=EngineConditionType(c.condition.value))
        for c in participant.conditions
    ]
    effects = [
        MechanicalEffectRead(
            effect_type=e.effect_type, value=e.value, target=e.target
        )
        for e in get_condition_effects(engine_conditions)
    ]
    return EncounterParticipantRead(
        id=participant.id,
        encounter_id=participant.encounter_id,
        character_id=participant.character_id,
        npc_id=participant.npc_id,
        name=participant.name,
        initiative=participant.initiative,
        hit_point_max=participant.hit_point_max,
        hit_point_current=participant.hit_point_current,
        temporary_hit_points=participant.temporary_hit_points,
        armor_class=participant.armor_class,
        turn_order=participant.turn_order,
        is_active=participant.is_active,
        conditions=[
            EncounterConditionRead.model_validate(c) for c in participant.conditions
        ],
        effects=effects,
    )


def encounter_to_read(encounter: Encounter) -> EncounterRead:
    """Build an encounter's read schema, with each participant's effects resolved."""
    return EncounterRead(
        id=encounter.id,
        session_id=encounter.session_id,
        name=encounter.name,
        status=encounter.status,
        current_round=encounter.current_round,
        current_turn_order=encounter.current_turn_order,
        created_at=encounter.created_at,
        participants=[participant_to_read(p) for p in encounter.participants],
    )


class CombatService:
    """Orchestrates encounter creation, participant management, and reads."""

    async def create_encounter(
        self,
        session_id: uuid.UUID,
        requester_id: uuid.UUID,
        data: EncounterCreate,
        db: AsyncSession,
    ) -> EncounterRead:
        """Create an encounter for a session; only the campaign's DM may do this."""
        session = await self._require_dm_for_session(session_id, requester_id, db)

        encounter = Encounter(session_id=session.id, name=data.name)
        db.add(encounter)
        await db.commit()
        return encounter_to_read(await self._reload_encounter(encounter.id, db))

    async def start_encounter(
        self, encounter_id: uuid.UUID, requester_id: uuid.UUID, db: AsyncSession
    ) -> EncounterRead:
        """Transition an encounter from `preparing` to `active`. DM only.

        Also auto-adds every campaign PC not already a participant, without
        an initiative — monsters/NPCs are still added manually. Nobody can
        advance turns until every active participant has rolled (see
        `advance_turn`).
        """
        encounter = await self._load_encounter_or_404(encounter_id, db)
        session = await self._require_dm_for_session(
            encounter.session_id, requester_id, db
        )

        if encounter.status != EncounterStatus.preparing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Only a preparing encounter can be started",
            )
        await self._add_missing_campaign_pcs(encounter, session.campaign_id, db)
        encounter.status = EncounterStatus.active
        encounter.current_round = 1
        await db.commit()
        return encounter_to_read(await self._reload_encounter(encounter.id, db))

    async def _add_missing_campaign_pcs(
        self, encounter: Encounter, campaign_id: uuid.UUID, db: AsyncSession
    ) -> None:
        """Add every campaign PC not already a participant, initiative unset."""
        existing_character_ids = {
            p.character_id for p in encounter.participants if p.character_id is not None
        }
        result = await db.execute(
            select(Character)
            .join(CampaignMember, CampaignMember.id == Character.campaign_member_id)
            .where(CampaignMember.campaign_id == campaign_id)
        )
        next_turn_order = (
            max((p.turn_order for p in encounter.participants), default=-1) + 1
        )
        for character in result.scalars().all():
            if character.id in existing_character_ids:
                continue
            db.add(
                EncounterParticipant(
                    encounter_id=encounter.id,
                    character_id=character.id,
                    name=character.name,
                    initiative=None,
                    hit_point_max=character.hit_point_max,
                    hit_point_current=character.hit_point_current,
                    armor_class=character.armor_class,
                    turn_order=next_turn_order,
                )
            )
            next_turn_order += 1

    async def list_encounters(
        self, session_id: uuid.UUID, requester_id: uuid.UUID, db: AsyncSession
    ) -> list[EncounterRead]:
        """List a session's encounters. Viewable by any campaign member."""
        session = await self._require_session(session_id, db)
        await self._require_membership(session.campaign_id, requester_id, db)

        result = await db.execute(
            select(Encounter)
            .where(Encounter.session_id == session_id)
            .options(*_ENCOUNTER_LOAD_OPTIONS)
            .order_by(Encounter.created_at)
        )
        return [encounter_to_read(e) for e in result.scalars().all()]

    async def get_encounter(
        self, encounter_id: uuid.UUID, requester_id: uuid.UUID, db: AsyncSession
    ) -> EncounterRead:
        """Get an encounter's detail. Viewable by any campaign member."""
        encounter, _member = await self.get_encounter_membership(
            encounter_id, requester_id, db
        )
        return encounter_to_read(encounter)

    async def get_encounter_membership(
        self, encounter_id: uuid.UUID, requester_id: uuid.UUID, db: AsyncSession
    ) -> tuple[Encounter, CampaignMember]:
        """Load an encounter (ORM row) plus the requester's campaign membership.

        Reused by the WebSocket handler to authenticate a connection and
        learn the requester's role (DM vs. player) in one call. Returns the
        raw ORM `Encounter` (not `EncounterRead`) — callers that need the
        read schema should use `get_encounter` instead.
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
    ) -> EncounterRead:
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
        participant = EncounterParticipant(
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
        db.add(participant)
        await db.flush()
        self._log(
            db,
            encounter,
            actor_id=participant.id,
            description=f"{participant.name} joined the encounter",
        )
        await db.commit()
        return encounter_to_read(await self._reload_encounter(encounter.id, db))

    async def update_participant(
        self,
        encounter_id: uuid.UUID,
        participant_id: uuid.UUID,
        requester_id: uuid.UUID,
        data: EncounterParticipantUpdate,
        db: AsyncSession,
    ) -> EncounterRead:
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
            self._log_hp_change(
                db, encounter, participant, data.hit_point_current
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
        return encounter_to_read(await self._reload_encounter(encounter.id, db))

    async def remove_participant(
        self,
        encounter_id: uuid.UUID,
        participant_id: uuid.UUID,
        requester_id: uuid.UUID,
        db: AsyncSession,
    ) -> EncounterRead:
        """Remove a participant from an encounter. DM only."""
        encounter = await self._load_encounter_or_404(encounter_id, db)
        await self._require_dm_for_session(encounter.session_id, requester_id, db)
        participant = self._find_participant_or_404(encounter, participant_id)

        self._log(
            db,
            encounter,
            actor_id=participant.id,
            description=f"{participant.name} left the encounter",
        )
        await db.delete(participant)
        await db.commit()
        return encounter_to_read(await self._reload_encounter(encounter.id, db))

    async def advance_turn(
        self, encounter_id: uuid.UUID, requester_id: uuid.UUID, db: AsyncSession
    ) -> tuple[EncounterRead, TurnAdvanceResult]:
        """Advance to the next active participant's turn (live, WS-driven). DM only.

        Rejected while any active participant hasn't rolled initiative yet
        (see `roll_initiative`) — 422, not blocked silently.
        """
        encounter = await self._load_encounter_or_404(encounter_id, db)
        await self._require_dm_for_session(encounter.session_id, requester_id, db)

        missing_initiative = [
            p for p in encounter.participants if p.is_active and p.initiative is None
        ]
        if missing_initiative:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=(
                    "All participants must roll initiative before turns can "
                    "advance"
                ),
            )

        turn_participants = [
            TurnParticipant(id=p.id, turn_order=p.turn_order, is_active=p.is_active)
            for p in encounter.participants
        ]
        result = compute_next_turn(
            turn_participants,
            current_round=encounter.current_round,
            current_turn_order=encounter.current_turn_order,
        )
        encounter.current_round = result.round
        encounter.current_turn_order = result.turn_order
        if result.participant_id is not None:
            next_up = next(
                p for p in encounter.participants if p.id == result.participant_id
            )
            self._log(
                db,
                encounter,
                actor_id=next_up.id,
                description=f"Round {result.round}: {next_up.name}'s turn",
            )
        await db.commit()
        reloaded = await self._reload_encounter(encounter.id, db)
        return encounter_to_read(reloaded), result

    async def end_encounter(
        self, encounter_id: uuid.UUID, requester_id: uuid.UUID, db: AsyncSession
    ) -> EncounterRead:
        """End an encounter (live, WS-driven): sets it to `completed`. DM only."""
        encounter = await self._load_encounter_or_404(encounter_id, db)
        await self._require_dm_for_session(encounter.session_id, requester_id, db)

        encounter.status = EncounterStatus.completed
        self._log(db, encounter, description="Encounter ended")
        await db.commit()
        return encounter_to_read(await self._reload_encounter(encounter.id, db))

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
    ) -> EncounterParticipantRead:
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
            self._log_hp_change(db, encounter, participant, hit_point_current)
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
                self._log(
                    db,
                    encounter,
                    target_id=participant.id,
                    description=(
                        f"{participant.name} gained condition: {add_condition}"
                    ),
                )
        if remove_condition is not None:
            for condition in list(participant.conditions):
                if condition.condition == remove_condition:
                    await db.delete(condition)
                    self._log(
                        db,
                        encounter,
                        target_id=participant.id,
                        description=(
                            f"{participant.name} lost condition: "
                            f"{remove_condition}"
                        ),
                    )

        await db.commit()
        result = await db.execute(
            select(EncounterParticipant)
            .where(EncounterParticipant.id == participant.id)
            .options(selectinload(EncounterParticipant.conditions))
            .execution_options(populate_existing=True)
        )
        return participant_to_read(result.scalar_one())

    async def roll_initiative(
        self,
        encounter_id: uuid.UUID,
        participant_id: uuid.UUID,
        requester_id: uuid.UUID,
        initiative: int,
        db: AsyncSession,
    ) -> EncounterParticipantRead:
        """Set a participant's initiative (live, WS-driven).

        Unlike other WS commands this isn't DM-only: a player may roll for
        their own character's participant; the DM may roll for any
        participant (their own characters, NPCs, monsters).
        """
        encounter = await self._load_encounter_or_404(encounter_id, db)
        session = await self._require_session(encounter.session_id, db)
        member = await self._require_membership(session.campaign_id, requester_id, db)
        participant = self._find_participant_or_404(encounter, participant_id)

        if member.role != CampaignRole.dm:
            owns = await self._participant_owned_by(participant, requester_id, db)
            if not owns:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only roll initiative for your own character",
                )

        participant.initiative = initiative
        self._log(
            db,
            encounter,
            actor_id=participant.id,
            description=f"{participant.name} rolled initiative: {initiative}",
        )
        await db.commit()
        result = await db.execute(
            select(EncounterParticipant)
            .where(EncounterParticipant.id == participant.id)
            .options(selectinload(EncounterParticipant.conditions))
            .execution_options(populate_existing=True)
        )
        return participant_to_read(result.scalar_one())

    async def _participant_owned_by(
        self,
        participant: EncounterParticipant,
        requester_id: uuid.UUID,
        db: AsyncSession,
    ) -> bool:
        """Whether `requester_id` owns the campaign membership behind `participant`."""
        if participant.character_id is None:
            return False
        result = await db.execute(
            select(Character).where(Character.id == participant.character_id)
        )
        character = result.scalar_one_or_none()
        if character is None:
            return False
        member_result = await db.execute(
            select(CampaignMember).where(
                CampaignMember.id == character.campaign_member_id
            )
        )
        member = member_result.scalar_one_or_none()
        return member is not None and member.user_id == requester_id

    async def get_log(
        self, encounter_id: uuid.UUID, requester_id: uuid.UUID, db: AsyncSession
    ) -> list[CombatLogRead]:
        """List an encounter's combat log, in chronological order. Any member."""
        encounter, _member = await self.get_encounter_membership(
            encounter_id, requester_id, db
        )
        result = await db.execute(
            select(CombatLog)
            .where(CombatLog.encounter_id == encounter.id)
            .order_by(CombatLog.created_at)
        )
        return [CombatLogRead.model_validate(log) for log in result.scalars().all()]

    def _log(
        self,
        db: AsyncSession,
        encounter: Encounter,
        *,
        description: str,
        actor_id: uuid.UUID | None = None,
        target_id: uuid.UUID | None = None,
        action_type: ActionType = ActionType.other,
        damage_dealt: int | None = None,
        damage_type: str | None = None,
    ) -> None:
        """Record one CombatLog entry at the encounter's current round/turn."""
        db.add(
            CombatLog(
                encounter_id=encounter.id,
                round=encounter.current_round,
                turn_order=encounter.current_turn_order,
                actor_id=actor_id,
                action_type=action_type,
                description=description,
                damage_dealt=damage_dealt,
                damage_type=damage_type,
                target_id=target_id,
            )
        )

    def _log_hp_change(
        self,
        db: AsyncSession,
        encounter: Encounter,
        participant: EncounterParticipant,
        new_hit_point_current: int,
    ) -> None:
        """Log a damage or heal entry from an HP change, skipping no-ops."""
        delta = new_hit_point_current - participant.hit_point_current
        if delta == 0:
            return
        if delta < 0:
            description = f"{participant.name} took {-delta} damage"
            damage_dealt = -delta
        else:
            description = f"{participant.name} healed {delta} HP"
            damage_dealt = None
        self._log(
            db,
            encounter,
            target_id=participant.id,
            description=description,
            damage_dealt=damage_dealt,
        )

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
