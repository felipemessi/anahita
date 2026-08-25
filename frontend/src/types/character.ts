/**
 * Mirrors backend/app/characters/schemas.py and domain.py.
 * Keep in sync manually — no codegen yet (PRD frontend backlog Fase 0).
 */

import type { AbilityScore } from "@/types/catalog";

export type Skill =
  | "acrobatics"
  | "animal_handling"
  | "arcana"
  | "athletics"
  | "deception"
  | "history"
  | "insight"
  | "intimidation"
  | "investigation"
  | "medicine"
  | "nature"
  | "perception"
  | "performance"
  | "persuasion"
  | "religion"
  | "sleight_of_hand"
  | "stealth"
  | "survival";

export interface CharacterAbilityScoreCreate {
  ability: AbilityScore;
  base_score: number;
  asi_bonus?: number;
  misc_bonus?: number;
}

/**
 * `modifier`, `save_bonus` are computed by the backend rules engine — never
 * persisted, only derived on read. `save_proficient` is set once at
 * character creation from the starting class's saving throw proficiencies.
 */
export interface CharacterAbilityScore {
  id: string;
  ability: AbilityScore;
  base_score: number;
  asi_bonus: number;
  misc_bonus: number;
  modifier: number;
  save_proficient: boolean;
  save_bonus: number;
}

/** `ability` and `bonus` are computed by the backend rules engine, never persisted. */
export interface CharacterSkill {
  id: string;
  skill: Skill;
  ability: AbilityScore;
  proficient: boolean;
  expertise: boolean;
  bonus: number;
}

export interface CharacterSpellCreate {
  spell_id: string;
  prepared?: boolean;
  source_class?: string | null;
}

/** Toggle a known spell's `prepared` flag (`PATCH .../spells/{spellId}`). */
export interface CharacterSpellUpdate {
  prepared: boolean;
}

/**
 * `level` (circle, 0 = cantrip) and `ritual` are resolved from the catalog
 * on read, never persisted — mirrors `CharacterSpellRead`.
 */
export interface CharacterSpell {
  id: string;
  spell_id: string;
  prepared: boolean;
  source_class: string | null;
  level: number;
  ritual: boolean;
}

/** Cast a known spell (`POST .../spells/{spellId}/cast`). */
export interface CharacterSpellCastRequest {
  /** Defaults to the spell's own level — set higher to upcast. */
  cast_at_level?: number | null;
  as_ritual?: boolean;
}

/** `max` is derived from the catalog on read, never persisted. */
export interface CharacterSpellSlot {
  spell_level: number;
  used: number;
  max: number;
}

export type RestType = "short" | "long";

export interface CharacterRestRequest {
  rest_type: RestType;
}

export interface CharacterEquipmentCreate {
  item_id: string;
  equipped?: boolean;
  quantity?: number;
  attunement?: boolean;
}

/** Every field optional — only the ones supplied are changed. */
export interface CharacterEquipmentUpdate {
  equipped?: boolean;
  attunement?: boolean;
  quantity?: number;
}

export interface CharacterEquipment {
  id: string;
  item_id: string;
  equipped: boolean;
  quantity: number;
  attunement: boolean;
}

/** Record a currency gain (positive `delta`) or spend (negative). */
export interface CharacterCurrencyRequest {
  delta: number;
}

export type FeatureSourceType = "class" | "feat";

export interface CharacterFeatureCreate {
  source_type: FeatureSourceType;
  source_name: string;
  feature_name: string;
  description?: string | null;
  level_acquired?: number;
}

export interface CharacterFeature {
  id: string;
  source_type: FeatureSourceType;
  source_name: string;
  feature_name: string;
  description: string | null;
  level_acquired: number;
}

export interface CharacterClassCreate {
  class_definition_id: string;
  subclass_id?: string | null;
  level?: number;
}

export interface CharacterClass {
  id: string;
  class_definition_id: string;
  subclass_id: string | null;
  level: number;
}

export interface CharacterCreate {
  campaign_member_id: string;
  name: string;
  race_id: string;
  subrace_id?: string | null;
  level?: number;
  experience_points?: number;
  alignment?: string | null;
  background?: string | null;
  temporary_hit_points?: number;
  inspiration?: boolean;
  ability_scores: CharacterAbilityScoreCreate[];
  classes: CharacterClassCreate[];
}

export interface Character {
  id: string;
  campaign_member_id: string;
  name: string;
  race_id: string;
  subrace_id: string | null;
  level: number;
  experience_points: number;
  alignment: string | null;
  background: string | null;
  hit_point_max: number;
  hit_point_current: number;
  temporary_hit_points: number;
  armor_class: number;
  speed: number;
  inspiration: boolean;
  proficiency_bonus: number;
  /** Normalized-copper balance (1 cp / 10 sp / 50 ep / 100 gp / 1000 pp). */
  currency_cp: number;
  ability_scores: CharacterAbilityScore[];
  skills: CharacterSkill[];
  classes: CharacterClass[];
  spells: CharacterSpell[];
  spell_slots: CharacterSpellSlot[];
  equipment: CharacterEquipment[];
  features: CharacterFeature[];
}

/**
 * What a player sees for another player's character on the campaign
 * roster — the owner and the DM get the full `Character` instead (see
 * `GET /characters?campaign_id=`, a `Character | CharacterSummary` union).
 */
export interface CharacterSummary {
  id: string;
  campaign_member_id: string;
  name: string;
  race_id: string;
  subrace_id: string | null;
  level: number;
  classes: CharacterClass[];
}

/** True for the fields only present on the full sheet, narrowing the union. */
export function isFullCharacter(
  character: Character | CharacterSummary,
): character is Character {
  return "hit_point_max" in character;
}
