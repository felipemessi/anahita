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

/** One class's hit dice spent during a short rest to recover HP. */
export interface CharacterHitDiceSpend {
  character_class_id: string;
  count: number;
  /** Pre-rolled total HP healed (already including the CON modifier). */
  manual_roll?: number;
}

export interface CharacterRestRequest {
  rest_type: RestType;
  /** Only applies to a short rest — one entry per class spending dice. */
  hit_dice_spent?: CharacterHitDiceSpend[];
}

/** One class's hit dice roll from a short rest, in request order (Fase 8). */
export interface CharacterHitDiceRollResult {
  character_class_id: string;
  roll_result: number;
  modifier: number;
  healed: number;
}

/**
 * Response for taking a rest: the updated character, plus any hit dice
 * rolled — `hit_dice_rolls` is empty for a long rest (dice are restored,
 * not rolled), used to drive the dice-roll animation for a short rest.
 */
export interface CharacterRestResponse {
  character: Character;
  hit_dice_rolls: CharacterHitDiceRollResult[];
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

/** A named option picked for a level-up choice feature (Fase 8). */
export interface CharacterFeatureChoice {
  id: string;
  feature_id: string;
  feature_option_id: string;
}

/** One pick sent back with `feature_choices` in `CharacterLevelUpRequest`. */
export interface CharacterFeatureChoiceInput {
  feature_id: string;
  feature_option_id: string;
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
  /** Hit dice spent for this class, out of a max of `level` (Fase 7). */
  hit_dice_used: number;
}

/** Request body to roll a death saving throw at 0 hit points (Fase 7). */
export interface CharacterDeathSaveRequest {
  /** Pre-rolled 1d20 result. */
  manual_roll?: number;
}

/**
 * Response for rolling a death saving throw: the updated character, plus
 * the raw 1d20 result — used to drive the dice-roll animation (Fase 8).
 */
export interface CharacterDeathSaveResponse {
  character: Character;
  roll_result: number;
}

/**
 * Request body to start or end concentration on a known spell (Fase 7).
 * `spell_id` unset ends concentration; set, it starts (replacing whatever
 * was already being concentrated on).
 */
export interface CharacterConcentrationRequest {
  spell_id?: string | null;
}

/** One class the character already has, or a new one via multiclass (Fase 7). */
export interface CharacterLevelUpRequest {
  class_definition_id: string;
  subclass_id?: string | null;
  /** Only at an ASI level — mutually exclusive with `feat_id`. */
  ability_score_increases?: Partial<Record<AbilityScore, number>>;
  feat_id?: string;
  /** Pre-rolled hit die result (before the CON modifier is added). */
  manual_hit_die_roll?: number;
  /**
   * One pick per choice feature granted at the new level (Fighting Style,
   * Pact Boon, Eldritch Invocations, ...). Required whenever the level
   * grants one — omitting it (or picking too few for a multi-pick
   * feature) gets a 422 whose `detail` is `RequiresChoiceDetail`.
   */
  feature_choices?: CharacterFeatureChoiceInput[];
}

/** A level-up feature's pending pick(s) — `detail` of a `requires_choice` 422. */
export interface PendingFeatureChoice {
  feature_id: string;
  required_count: number;
  options: { id: string; name: string }[];
}

export interface RequiresChoiceDetail {
  requires_choice: true;
  choices: PendingFeatureChoice[];
}

/**
 * A trackable class resource (rage, ki, ...) — `max` is derived from the
 * catalog on read, never persisted (Fase 7).
 */
export interface CharacterResource {
  resource_key: string;
  used: number;
  max: number;
}

/**
 * How a player generated a character's base ability scores (Fase 8) —
 * `point_buy` and `standard_array` are validated server-side against the
 * PHB rules; `custom`/`roll` accept any values, the client decides.
 */
export type AbilityGenerationMethod = "standard_array" | "point_buy" | "custom" | "roll";

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
  generation_method?: AbilityGenerationMethod | null;
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
  /** 0-3, reset on stabilizing/healing (Fase 7). */
  death_save_successes: number;
  death_save_failures: number;
  is_dead: boolean;
  /** The spell currently being concentrated on, if any (Fase 7). */
  concentrating_spell_id: string | null;
  /** `10 + bonus` of the corresponding skill, computed on read (Fase 7). */
  passive_perception: number;
  passive_investigation: number;
  passive_insight: number;
  resources: CharacterResource[];
  ability_scores: CharacterAbilityScore[];
  skills: CharacterSkill[];
  classes: CharacterClass[];
  spells: CharacterSpell[];
  spell_slots: CharacterSpellSlot[];
  equipment: CharacterEquipment[];
  features: CharacterFeature[];
  feature_choices: CharacterFeatureChoice[];
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
