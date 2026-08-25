"""SQLAlchemy models for the combat domain: live encounters (PRD §7.6)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.combat.domain import ActionType, ConditionType, EncounterStatus
from app.database import Base


class Encounter(Base):
    """A combat encounter within a session, tracking round/turn state."""

    __tablename__ = "encounters"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("sessions.id"))
    name: Mapped[str] = mapped_column(String(255))
    status: Mapped[EncounterStatus] = mapped_column(
        SAEnum(EncounterStatus, name="encounterstatus"),
        default=EncounterStatus.preparing,
    )
    current_round: Mapped[int] = mapped_column(Integer, default=1)
    current_turn_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    participants: Mapped[list[EncounterParticipant]] = relationship(
        back_populates="encounter", cascade="all, delete-orphan"
    )
    logs: Mapped[list[CombatLog]] = relationship(
        back_populates="encounter", cascade="all, delete-orphan"
    )


class EncounterParticipant(Base):
    """A combatant in an encounter: a PC, an NPC/monster, or an ad-hoc entry.

    `character_id` and `npc_id` are mutually exclusive (never both set) —
    enforced in `app.combat.domain.validate_participant_kind`, not at the DB
    level (SQLite test DBs don't share Postgres's partial-index/CHECK
    ergonomics — mirrors how `app.characters.domain` validates catalog
    references at the application layer).
    """

    __tablename__ = "encounter_participants"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    encounter_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("encounters.id")
    )
    character_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("characters.id")
    )
    # FK to a future `npcs.id` (World-building, Fase 3, not yet implemented) —
    # omitted here to avoid coupling to a domain that doesn't exist yet, same
    # pattern as `app.catalog.models.Race.campaign_id`.
    npc_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    name: Mapped[str] = mapped_column(String(255))
    # Nullable: PCs auto-added by `CombatService.start_encounter` and manual
    # participants alike start without a roll — `advance_turn` refuses to
    # proceed while any active participant's initiative is still unset (see
    # `CombatService.advance_turn`), and the `roll_initiative` WS command is
    # the only way to set it (PRD §10.2, backlog Fase 6 história 4).
    initiative: Mapped[int | None] = mapped_column(Integer, nullable=True)
    hit_point_max: Mapped[int] = mapped_column(Integer)
    hit_point_current: Mapped[int] = mapped_column(Integer)
    temporary_hit_points: Mapped[int] = mapped_column(Integer, default=0)
    armor_class: Mapped[int] = mapped_column(Integer)
    turn_order: Mapped[int] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    encounter: Mapped[Encounter] = relationship(back_populates="participants")
    conditions: Mapped[list[EncounterCondition]] = relationship(
        back_populates="participant", cascade="all, delete-orphan"
    )


class EncounterCondition(Base):
    """A 5e condition currently affecting an EncounterParticipant."""

    __tablename__ = "encounter_conditions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    participant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("encounter_participants.id")
    )
    condition: Mapped[ConditionType] = mapped_column(
        SAEnum(ConditionType, name="combatconditiontype")
    )
    duration_rounds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    applied_at_round: Mapped[int] = mapped_column(Integer)

    participant: Mapped[EncounterParticipant] = relationship(
        back_populates="conditions"
    )


class CombatLog(Base):
    """One logged action during an encounter, for post-session reference.

    `actor_id`/`target_id` are `ON DELETE SET NULL` (not a plain FK like the
    PRD table implies) — a log entry must outlive the participant it refers
    to (removing a fled/dead participant is a normal `remove_participant`
    action, PRD §10.2), so the reference is nulled out rather than the log
    row being lost or blocking the delete.
    """

    __tablename__ = "combat_logs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    encounter_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("encounters.id")
    )
    round: Mapped[int] = mapped_column(Integer)
    turn_order: Mapped[int] = mapped_column(Integer)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("encounter_participants.id", ondelete="SET NULL"),
        nullable=True,
    )
    action_type: Mapped[ActionType] = mapped_column(
        SAEnum(ActionType, name="combatactiontype")
    )
    description: Mapped[str] = mapped_column(Text)
    damage_dealt: Mapped[int | None] = mapped_column(Integer, nullable=True)
    damage_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    target_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("encounter_participants.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    encounter: Mapped[Encounter] = relationship(back_populates="logs")
