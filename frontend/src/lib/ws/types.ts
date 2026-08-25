/**
 * Message shapes for `/ws/combat/{encounter_id}` — mirrors
 * backend/app/combat/ws_router.py and schemas.py §"WebSocket message
 * payloads". Envelope: `{"event_type": "...", "payload": {...}}`.
 */

import type {
  CombatActionType,
  Condition,
  Encounter,
  EncounterParticipant,
  EncounterParticipantCreate,
  EncounterStatus,
} from "@/types/combat";
import type { HandoutRevealedPayload } from "@/types/handout";

export interface TurnAdvancedPayload {
  round: number;
  turn_order: number;
  participant_id: string | null;
}

export interface EncounterStatusChangedPayload {
  status: EncounterStatus;
}

export interface WSErrorPayload {
  detail: string;
}

/** Response payload for the `declare_action` command — mirrors `DeclareActionResultRead`. */
export interface DeclareActionResult {
  actor_id: string;
  target_id: string;
  action_type: CombatActionType;
  attack_roll: number | null;
  attack_bonus: number | null;
  hit: boolean | null;
  damage_rolled: number | null;
  damage_type: string | null;
  condition_applied: string | null;
  attacker_check: number | null;
  target_check: number | null;
  description: string;
}

/** Server → client events. */
export type CombatServerEvent =
  | { event_type: "state_sync"; payload: Encounter }
  | { event_type: "turn_advanced"; payload: TurnAdvancedPayload }
  | { event_type: "participant_updated"; payload: EncounterParticipant }
  | { event_type: "encounter_status_changed"; payload: EncounterStatusChangedPayload }
  | { event_type: "action_resolved"; payload: DeclareActionResult }
  // Broadcast by app.handouts.service over this same combat socket (PRD §10.3),
  // not by the combat domain itself — kept here rather than duplicating the
  // socket/reconnect machinery in lib/ws/combat-socket.ts for a second event source.
  | { event_type: "handout_revealed"; payload: HandoutRevealedPayload }
  | { event_type: "error"; payload: WSErrorPayload };

/** Payload for the `update_participant` command — damage/heal/AC/condition. */
export interface WSUpdateParticipantPayload {
  participant_id: string;
  hit_point_current?: number;
  temporary_hit_points?: number;
  armor_class?: number;
  add_condition?: Condition;
  remove_condition?: Condition;
}

export interface WSRemoveParticipantPayload {
  participant_id: string;
}

/**
 * Payload for the `roll_initiative` command — unlike the other commands,
 * not DM-only (a player may send it for their own participant, the DM for
 * any). `initiative` omitted rolls `1d20 + DEX` server-side.
 */
export interface WSRollInitiativePayload {
  participant_id: string;
  initiative?: number;
}

/**
 * Payload for the `declare_action` command — also not DM-only. See
 * `app.combat.schemas.WSDeclareActionPayload` for the full field docs
 * (weapon/spell/monster-action selectors, manual overrides).
 */
export interface WSDeclareActionPayload {
  participant_id: string;
  target_id: string;
  action_type: CombatActionType;
  weapon_equipment_id?: string;
  spell_entry_id?: string;
  cast_at_level?: number;
  monster_action_id?: string;
  manual_attack_bonus?: number;
  manual_damage_expression?: string;
  manual_athletics_bonus?: number;
  manual_target_bonus?: number;
  manual_attack_roll?: number;
  manual_damage_roll?: number;
  manual_target_roll?: number;
}

/** Client (DM only) → server commands. */
export type CombatClientCommand =
  | { event_type: "advance_turn"; payload?: Record<string, never> }
  | { event_type: "update_participant"; payload: WSUpdateParticipantPayload }
  | { event_type: "add_participant"; payload: EncounterParticipantCreate }
  | { event_type: "remove_participant"; payload: WSRemoveParticipantPayload }
  | { event_type: "end_encounter"; payload?: Record<string, never> }
  // Client (any campaign member) → server commands.
  | { event_type: "roll_initiative"; payload: WSRollInitiativePayload }
  | { event_type: "declare_action"; payload: WSDeclareActionPayload };
