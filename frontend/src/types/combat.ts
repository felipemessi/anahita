/**
 * PROVISIONAL — the backend `combat` domain (Fase 2) does not exist yet, so
 * there is no schemas.py to mirror. Shapes here follow
 * docs/anahita-backend-prd.md §7.6 and §10.2 (WebSocket protocol). Re-verify
 * against the real Pydantic schemas once the backend domain ships.
 */

export type EncounterStatus = "preparing" | "active" | "completed";

export interface Encounter {
  id: string;
  session_id: string;
  name: string;
  status: EncounterStatus;
  current_round: number;
  current_turn_order: number;
  created_at: string;
}

/** A participant is a PC *or* an NPC, never both — enforced at the application layer. */
export interface EncounterParticipant {
  id: string;
  encounter_id: string;
  character_id: string | null;
  npc_id: string | null;
  /** Fallback display name for generic monsters without a linked NPC. */
  name: string;
  initiative: number;
  hit_point_max: number;
  hit_point_current: number;
  temporary_hit_points: number;
  armor_class: number;
  turn_order: number;
  /** false = dead/fled. */
  is_active: boolean;
  conditions: EncounterCondition[];
}

/** The 15 D&D 5e conditions (PRD §7.6). */
export type Condition =
  | "blinded"
  | "charmed"
  | "deafened"
  | "exhaustion"
  | "frightened"
  | "grappled"
  | "incapacitated"
  | "invisible"
  | "paralyzed"
  | "petrified"
  | "poisoned"
  | "prone"
  | "restrained"
  | "stunned"
  | "unconscious";

export interface EncounterCondition {
  id: string;
  participant_id: string;
  condition: Condition;
  /** null = indefinite. */
  duration_rounds: number | null;
  applied_at_round: number;
}

export type CombatActionType =
  | "attack"
  | "spell"
  | "move"
  | "dash"
  | "dodge"
  | "disengage"
  | "help"
  | "hide"
  | "ready"
  | "other";

export interface CombatLogEntry {
  id: string;
  encounter_id: string;
  round: number;
  turn_order: number;
  actor_id: string;
  action_type: CombatActionType;
  description: string;
  damage_dealt: number | null;
  damage_type: string | null;
  target_id: string | null;
  created_at: string;
}
