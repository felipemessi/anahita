"""Pydantic request/response schemas for the combat domain."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.combat.domain import ActionType, ConditionType, EncounterStatus


class EncounterCreate(BaseModel):
    """Request body to create an encounter within a session."""

    name: str = Field(min_length=1, max_length=255)


class EncounterParticipantCreate(BaseModel):
    """Request body to add a participant to an encounter.

    `character_id`/`npc_id`/`monster_id` are mutually exclusive — see
    `app.combat.domain.validate_participant_kind`. None set means a
    manual/generic entry, identified only by `name`. `monster_id` links a
    catalog stat block — `declare_action` resolves attack/skill bonuses
    from it automatically; the other two kinds don't carry that data yet
    and require the declaring client to supply bonuses explicitly.
    """

    character_id: uuid.UUID | None = None
    npc_id: uuid.UUID | None = None
    monster_id: uuid.UUID | None = None
    name: str = Field(min_length=1, max_length=255)
    initiative: int | None = None
    hit_point_max: int = Field(ge=1)
    hit_point_current: int | None = Field(default=None, ge=0)
    armor_class: int = Field(ge=0)
    turn_order: int


class EncounterParticipantUpdate(BaseModel):
    """Request body to update a participant outside the live turn flow.

    Every field is optional — only the ones supplied are changed (mirrors
    `characters.schemas.CharacterUpdate`).
    """

    hit_point_current: int | None = Field(default=None, ge=0)
    temporary_hit_points: int | None = Field(default=None, ge=0)
    armor_class: int | None = Field(default=None, ge=0)
    initiative: int | None = None
    turn_order: int | None = None
    is_active: bool | None = None


class EncounterConditionRead(BaseModel):
    """Response schema for a condition affecting a participant."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    condition: ConditionType
    duration_rounds: int | None
    applied_at_round: int


class MechanicalEffectRead(BaseModel):
    """A resolved mechanical effect from one of a participant's active conditions.

    Mirrors `engine.types.MechanicalEffect` — computed by
    `engine.conditions.get_condition_effects` from `EncounterParticipant.
    conditions`, never persisted (same "compute on read" pattern as
    `CharacterAbilityScoreRead.modifier`).
    """

    effect_type: str
    value: int | str | None
    target: str | None


class EncounterParticipantRead(BaseModel):
    """Response schema for an encounter participant."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    encounter_id: uuid.UUID
    character_id: uuid.UUID | None
    npc_id: uuid.UUID | None
    monster_id: uuid.UUID | None
    name: str
    initiative: int | None
    hit_point_max: int
    hit_point_current: int
    temporary_hit_points: int
    armor_class: int
    turn_order: int
    is_active: bool
    conditions: list[EncounterConditionRead]
    effects: list[MechanicalEffectRead]
    # Only set when this update just dealt damage to a participant who was
    # concentrating on a spell — the client resolves the CON saving throw
    # itself (Fase 7); `max(10, damage // 2)`, PHB rule.
    concentration_dc: int | None = None
    # Legendary actions/reactions spent this round (Fase 7) — meaningful
    # only for an NPC/monster participant; reset at the start of its turn.
    legendary_actions_used: int = 0
    reactions_used: int = 0


class CombatLogRead(BaseModel):
    """Response schema for one logged combat action (PRD §7.6, história 4).

    `actor_id`/`target_id` are `ON DELETE SET NULL` — a removed participant
    doesn't take its history with it, see `app.combat.models.CombatLog`.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    encounter_id: uuid.UUID
    round: int
    turn_order: int
    actor_id: uuid.UUID | None
    action_type: ActionType
    description: str
    damage_dealt: int | None
    damage_type: str | None
    target_id: uuid.UUID | None
    rolled_by_system: bool
    created_at: datetime


class EncounterRead(BaseModel):
    """Response schema for an encounter, with its participants."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    session_id: uuid.UUID
    name: str
    status: EncounterStatus
    current_round: int
    current_turn_order: int
    created_at: datetime
    participants: list[EncounterParticipantRead]


# --- WebSocket message payloads (PRD §10.2) -----------------------------------
#
# Envelope: `{"event_type": "...", "payload": {...}}`. DM-only commands
# (client -> server): advance_turn, update_participant, add_participant,
# remove_participant, end_encounter. Server -> clients: state_sync,
# turn_advanced, participant_updated, encounter_status_changed.


class WSUpdateParticipantPayload(BaseModel):
    """Payload for the `update_participant` command — damage/heal/condition."""

    participant_id: uuid.UUID
    hit_point_current: int | None = Field(default=None, ge=0)
    temporary_hit_points: int | None = Field(default=None, ge=0)
    armor_class: int | None = Field(default=None, ge=0)
    add_condition: ConditionType | None = None
    remove_condition: ConditionType | None = None


class WSRemoveParticipantPayload(BaseModel):
    """Payload for the `remove_participant` command."""

    participant_id: uuid.UUID


class WSDeclareActionPayload(BaseModel):
    """Payload for the `declare_action` command — attack/grapple/shove.

    Resolved automatically when the attacker is a Character (via
    `weapon_equipment_id`/`spell_entry_id`, selecting from their own sheet)
    or a catalog-linked Monster (via `monster_action_id`); a purely manual
    participant (no `character_id`/`monster_id`) has no stat block to
    resolve from, so the declaring client must supply `manual_attack_bonus`
    + `manual_damage_expression` (attacks) or `manual_athletics_bonus`
    (grapple/shove) instead — `declare_action` rejects (422) with a clear
    message when neither is available. The same manual/auto split applies
    to the *target* of a grapple/shove (`manual_target_bonus`), since the
    opposed check needs a bonus from both sides.

    `manual_attack_roll`/`manual_damage_roll` (and `manual_target_roll` for
    the defender's side of a grapple/shove contest) let the declaring
    player type in a result instead of the server rolling via
    `engine/dice.py` (backlog Fase 6 história 6) — a player may only supply
    these for their own participant, the DM for any (mirrors
    `roll_initiative`).

    `use_class_resource` (Fase 12) spends one use of a character's class
    resource (`resource_key`, e.g. `channel_divinity_charges`) via
    `CharacterService.use_resource` — same owner-only rule as that service
    method, so a DM declaring this on a player's behalf still gets a 403
    (unlike attacks/contests, which the DM may always declare). Only
    Character participants have a resource to spend. `resource_option_id`
    picks the named option when the resource has more than one (mirrors
    `use_resource`'s own `option_id`) — for Channel Divinity: Turn Undead
    specifically, it's also how the server knows to resolve the Wisdom
    saving throw effect below, rather than treat the use as bookkeeping
    only. `target_id` plus `additional_target_ids` name every undead
    affected — this app has no area/map geometry yet (Fase 15), so "every
    undead within 30 feet" is deliberately simplified to "whichever
    participants the declaring client lists", each rolling a Wisdom save
    (or taking `manual_save_rolls[participant_id]`) against the caster's
    spell save DC; a failure applies `frightened` (not the PHB's "turned"
    state, which this app's condition model doesn't have) for 1
    minute/10 rounds. Auto-destroying low-CR undead at higher Cleric
    levels isn't modeled.
    """

    participant_id: uuid.UUID
    target_id: uuid.UUID
    action_type: ActionType
    weapon_equipment_id: uuid.UUID | None = None
    spell_entry_id: uuid.UUID | None = None
    cast_at_level: int | None = Field(default=None, ge=1, le=9)
    monster_action_id: uuid.UUID | None = None
    manual_attack_bonus: int | None = None
    manual_damage_expression: str | None = None
    manual_athletics_bonus: int | None = None
    manual_target_bonus: int | None = None
    manual_attack_roll: int | None = None
    manual_damage_roll: int | None = None
    manual_target_roll: int | None = None
    resource_key: str | None = None
    resource_option_id: uuid.UUID | None = None
    additional_target_ids: list[uuid.UUID] = Field(default_factory=list)
    manual_save_rolls: dict[uuid.UUID, int] | None = None


class ClassResourceTargetOutcome(BaseModel):
    """One target's Wisdom save outcome from a `use_class_resource` effect.

    Only populated for a resource option with a mapped mechanical effect
    (Channel Divinity: Turn Undead, so far) — see `WSDeclareActionPayload`'s
    docstring.
    """

    participant_id: uuid.UUID
    save_roll: int
    save_dc: int
    succeeded: bool
    condition_applied: str | None = None


class DeclareActionResultRead(BaseModel):
    """Response schema for a resolved combat action (WS `action_resolved` event)."""

    actor_id: uuid.UUID
    target_id: uuid.UUID
    action_type: ActionType
    attack_roll: int | None = None
    attack_bonus: int | None = None
    hit: bool | None = None
    damage_rolled: int | None = None
    damage_type: str | None = None
    condition_applied: str | None = None
    attacker_check: int | None = None
    target_check: int | None = None
    description: str
    # Same convention as `EncounterParticipantRead.concentration_dc`.
    concentration_dc: int | None = None
    # `use_class_resource` only (Fase 12) — which resource was spent, and
    # each affected target's saving throw outcome (empty when the option
    # has no mapped mechanical effect — bookkeeping-only spend).
    resource_key: str | None = None
    resource_targets: list[ClassResourceTargetOutcome] = Field(default_factory=list)


class WSUseLegendaryActionPayload(BaseModel):
    """Payload for the `use_legendary_action` command (Fase 7). DM only.

    Only for an NPC/monster participant, and only outside its own turn
    (PHB rule) — resolved from `MonsterLegendaryAction`
    (`catalog_monster_legendary_actions`, via the acting participant's
    stat block) the same way `declare_action` resolves a monster's normal
    attack. Every stat block gets a flat 3-per-round budget — the SRD data
    this app seeds from doesn't carry a per-monster override, a documented
    simplification (see `CombatService._LEGENDARY_ACTIONS_PER_ROUND`).
    """

    participant_id: uuid.UUID
    target_id: uuid.UUID
    legendary_action_id: uuid.UUID
    manual_attack_roll: int | None = None
    manual_damage_roll: int | None = None


class WSTriggerReactionPayload(BaseModel):
    """Payload for the `trigger_reaction` command (Fase 7). DM only.

    Only for an NPC/monster participant, once per round — resolved from
    `MonsterReaction` the same way a legendary action is.
    """

    participant_id: uuid.UUID
    target_id: uuid.UUID
    reaction_id: uuid.UUID
    manual_attack_roll: int | None = None
    manual_damage_roll: int | None = None


class WSRollInitiativePayload(BaseModel):
    """Payload for the `roll_initiative` command.

    Unlike the other WS commands this one isn't DM-only: a player may send
    it for their own character's participant; the DM may send it for any
    participant (see `CombatService.roll_initiative`). `initiative` is
    optional — omitted, the server rolls `1d20 + DEX modifier` via
    `engine/dice.py` (Character or catalog-linked Monster only; a purely
    manual participant has no DEX to roll with and must supply it);
    supplied, it's used as-is and the roll is logged as manual (backlog
    Fase 6 história 6).
    """

    participant_id: uuid.UUID
    initiative: int | None = None
