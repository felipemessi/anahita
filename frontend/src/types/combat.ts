/**
 * Mirrors backend/app/combat/schemas.py and domain.py (Fase 2 do backend,
 * concluída — este arquivo era provisório antes disso, ver histórico).
 */

export type EncounterStatus = "preparing" | "active" | "completed";

/** The 15 D&D 5e conditions — mirrors `app.combat.domain.ConditionType`. */
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
  condition: Condition;
  /** null = indefinite. */
  duration_rounds: number | null;
  applied_at_round: number;
}

/**
 * A resolved mechanical effect from one of a participant's active
 * conditions — computed on read by `engine.conditions.get_condition_effects`,
 * never persisted (mirrors `MechanicalEffectRead`).
 */
export interface MechanicalEffect {
  effect_type: string;
  value: number | string | null;
  target: string | null;
}

/**
 * A participant is a PC, an NPC, *or* a catalog monster — never more than
 * one. None of the three set is a purely manual/generic entry.
 */
export interface EncounterParticipant {
  id: string;
  encounter_id: string;
  character_id: string | null;
  npc_id: string | null;
  /** A catalog stat block — `declare_action` resolves bonuses from it automatically. */
  monster_id: string | null;
  /** Fallback display name for generic monsters without a linked NPC. */
  name: string;
  /** null until `roll_initiative` — `advance_turn` is rejected while any active participant is still null. */
  initiative: number | null;
  hit_point_max: number;
  hit_point_current: number;
  temporary_hit_points: number;
  armor_class: number;
  turn_order: number;
  /** false = dead/fled. */
  is_active: boolean;
  conditions: EncounterCondition[];
  effects: MechanicalEffect[];
}

export interface Encounter {
  id: string;
  session_id: string;
  name: string;
  status: EncounterStatus;
  current_round: number;
  current_turn_order: number;
  created_at: string;
  participants: EncounterParticipant[];
}

export interface EncounterCreate {
  name: string;
}

/**
 * `character_id`/`npc_id`/`monster_id` are mutually exclusive; leaving all
 * three unset is a manual/generic entry identified only by `name`.
 */
export interface EncounterParticipantCreate {
  character_id?: string | null;
  npc_id?: string | null;
  monster_id?: string | null;
  name: string;
  /** Optional — a PC auto-added by `start_encounter` has none until it rolls. */
  initiative?: number | null;
  hit_point_max: number;
  hit_point_current?: number | null;
  armor_class: number;
  turn_order: number;
}

/** Every field optional — only the ones supplied are changed. */
export interface EncounterParticipantUpdate {
  hit_point_current?: number | null;
  temporary_hit_points?: number | null;
  armor_class?: number | null;
  initiative?: number | null;
  turn_order?: number | null;
  is_active?: boolean | null;
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
  | "attack_weapon"
  | "attack_spell"
  | "grapple"
  | "shove"
  | "search"
  | "other";

export interface CombatLogEntry {
  id: string;
  encounter_id: string;
  round: number;
  turn_order: number;
  /** null when the acting participant was later removed (ON DELETE SET NULL). */
  actor_id: string | null;
  action_type: CombatActionType;
  description: string;
  damage_dealt: number | null;
  damage_type: string | null;
  /** false when any roll this entry describes came from a manual value instead of the server rolling. */
  rolled_by_system: boolean;
  /** null when the target participant was later removed (ON DELETE SET NULL). */
  target_id: string | null;
  created_at: string;
}
