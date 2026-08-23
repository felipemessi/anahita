/**
 * Message shapes for `/ws/combat/{encounter_id}` — mirrors
 * backend/app/combat/ws_router.py and schemas.py §"WebSocket message
 * payloads". Envelope: `{"event_type": "...", "payload": {...}}`.
 */

import type {
  Condition,
  Encounter,
  EncounterParticipant,
  EncounterParticipantCreate,
  EncounterStatus,
} from "@/types/combat";

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

/** Server → client events. */
export type CombatServerEvent =
  | { event_type: "state_sync"; payload: Encounter }
  | { event_type: "turn_advanced"; payload: TurnAdvancedPayload }
  | { event_type: "participant_updated"; payload: EncounterParticipant }
  | { event_type: "encounter_status_changed"; payload: EncounterStatusChangedPayload }
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

/** Client (DM only) → server commands. */
export type CombatClientCommand =
  | { event_type: "advance_turn"; payload?: Record<string, never> }
  | { event_type: "update_participant"; payload: WSUpdateParticipantPayload }
  | { event_type: "add_participant"; payload: EncounterParticipantCreate }
  | { event_type: "remove_participant"; payload: WSRemoveParticipantPayload }
  | { event_type: "end_encounter"; payload?: Record<string, never> };
