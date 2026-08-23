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

/** `modifier` is computed by the backend rules engine — never persisted, only derived on read. */
export interface CharacterAbilityScore {
  id: string;
  ability: AbilityScore;
  base_score: number;
  asi_bonus: number;
  misc_bonus: number;
  modifier: number;
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

export interface CharacterSpell {
  id: string;
  spell_id: string;
  prepared: boolean;
  source_class: string | null;
}

export interface CharacterEquipmentCreate {
  item_id: string;
  equipped?: boolean;
  quantity?: number;
  attunement?: boolean;
}

export interface CharacterEquipment {
  id: string;
  item_id: string;
  equipped: boolean;
  quantity: number;
  attunement: boolean;
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
  ability_scores: CharacterAbilityScore[];
  skills: CharacterSkill[];
  classes: CharacterClass[];
  spells: CharacterSpell[];
  equipment: CharacterEquipment[];
  features: CharacterFeature[];
}
