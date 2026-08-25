/**
 * Mirrors backend/app/catalog/schemas.py and domain.py.
 * Keep in sync manually — no codegen yet (PRD frontend backlog Fase 0).
 *
 * Every text field (`name`, `description`, …) is already resolved server-side
 * to the requested `?locale=` — there is no raw `translations` blob on the
 * wire (see lib/api/client.ts / server.ts `locale` option and PRD §3.4).
 */

// --- Enums (catalog/domain.py) ----------------------------------------------

export type CreatureSize =
  | "tiny"
  | "small"
  | "medium"
  | "large"
  | "huge"
  | "gargantuan";

export type AbilityScore = "str" | "dex" | "con" | "int" | "wis" | "cha";

export type SpellSchool =
  | "abjuration"
  | "conjuration"
  | "divination"
  | "enchantment"
  | "evocation"
  | "illusion"
  | "necromancy"
  | "transmutation";

export type ItemType = "weapon" | "armor" | "gear" | "tool" | "consumable";

export type ItemRarity =
  | "common"
  | "uncommon"
  | "rare"
  | "very_rare"
  | "legendary"
  | "artifact";

export type DamageType =
  | "acid"
  | "bludgeoning"
  | "cold"
  | "fire"
  | "force"
  | "lightning"
  | "necrotic"
  | "piercing"
  | "poison"
  | "psychic"
  | "radiant"
  | "slashing"
  | "thunder";

export type LanguageType = "standard" | "exotic";

export type FeaturePrerequisiteType = "level" | "feature" | "spell";

export type DamageModifierType = "vulnerable" | "resistant" | "immune";

export type ProficiencyType =
  | "skill"
  | "saving_throw"
  | "weapon"
  | "armor"
  | "tool"
  | "other";

// --- Races -------------------------------------------------------------------

export interface RaceTrait {
  id: string;
  trait_name: string;
  description: string;
  mechanical_effect: string | null;
}

export interface SubraceTrait {
  id: string;
  trait_name: string;
  description: string;
  mechanical_effect: string | null;
}

export interface RaceAbilityBonus {
  id: string;
  ability: string;
  bonus: number;
}

export interface Subrace {
  id: string;
  index: string | null;
  name: string;
  description: string;
  traits: SubraceTrait[];
  ability_bonuses: RaceAbilityBonus[];
}

export interface Race {
  id: string;
  index: string | null;
  name: string;
  description: string;
  age: string;
  alignment_desc: string;
  size_description: string;
  language_desc: string;
  speed: number;
  size: string;
  darkvision_range: number;
  is_custom: boolean;
  traits: RaceTrait[];
  subraces: Subrace[];
  ability_bonuses: RaceAbilityBonus[];
}

export interface RaceSummary {
  id: string;
  index: string | null;
  name: string;
  speed: number;
  size: string;
  darkvision_range: number;
  is_custom: boolean;
}

// --- Classes -------------------------------------------------------------------

export interface FeaturePrerequisite {
  id: string;
  prerequisite_type: string;
  level: number | null;
  required_feature_id: string | null;
  spell_id: string | null;
}

export interface Feature {
  id: string;
  index: string | null;
  level: number;
  feature_name: string;
  description: string;
  mechanical_effect: string | null;
  parent_feature_id: string | null;
  prerequisites: FeaturePrerequisite[];
}

export interface ClassLevelSpellSlot {
  id: string;
  spell_level: number;
  slot_count: number;
}

export interface ClassLevelResource {
  id: string;
  resource_key: string;
  value: string;
}

export interface ClassLevel {
  id: string;
  level: number;
  proficiency_bonus: number | null;
  ability_score_bonuses: number | null;
  features: Feature[];
  spell_slots: ClassLevelSpellSlot[];
  resources: ClassLevelResource[];
}

export interface Subclass {
  id: string;
  index: string | null;
  name: string;
  description: string;
  flavor: string;
  is_custom: boolean;
  features: Feature[];
}

export interface ClassDefinition {
  id: string;
  index: string | null;
  name: string;
  hit_die: number;
  primary_ability: string;
  saving_throw_proficiencies: string;
  is_custom: boolean;
  levels: ClassLevel[];
  subclasses: Subclass[];
}

export interface ClassSummary {
  id: string;
  index: string | null;
  name: string;
  hit_die: number;
  primary_ability: string;
  is_custom: boolean;
}

// --- Spells -------------------------------------------------------------------

export interface SpellClassRef {
  id: string;
  name: string;
}

/**
 * `scaling_key` is a slot level (1-9) when `scaling_type=slot_level`, or a
 * character-level threshold (1/5/11/17) when `scaling_type=character_level`
 * (cantrips). `dice_expression` may contain the literal `"MOD"` token
 * (e.g. `"1d8 + MOD"`) — substituted server-side, never evaluated here.
 */
export interface SpellDamage {
  id: string;
  damage_type: string;
  scaling_type: "slot_level" | "character_level";
  scaling_key: number;
  dice_expression: string;
}

export interface Spell {
  id: string;
  index: string | null;
  name: string;
  level: number;
  school: string;
  casting_time: string;
  range: string;
  duration: string;
  components: string;
  ritual: boolean;
  concentration: boolean;
  description: string;
  higher_levels: string | null;
  is_custom: boolean;
  classes: SpellClassRef[];
  damages: SpellDamage[];
}

export interface SpellSummary {
  id: string;
  index: string | null;
  name: string;
  level: number;
  school: string;
  ritual: boolean;
  concentration: boolean;
  is_custom: boolean;
}

// --- Equipment -------------------------------------------------------------------

export interface WeaponDetail {
  id: string;
  damage_dice: string;
  damage_type: string;
  weapon_range: string;
}

export interface ArmorDetail {
  id: string;
  base_ac: number;
  dex_bonus_cap: number | null;
  stealth_disadvantage: boolean;
  strength_requirement: number | null;
}

export interface ItemProperty {
  id: string;
  name: string;
}

export interface Item {
  id: string;
  index: string | null;
  name: string;
  item_type: string;
  equipment_category: string;
  rarity: string | null;
  weight: number;
  cost: number;
  description: string;
  is_custom: boolean;
  properties: ItemProperty[];
  weapon_detail: WeaponDetail | null;
  armor_detail: ArmorDetail | null;
}

export interface ItemSummary {
  id: string;
  index: string | null;
  name: string;
  item_type: string;
  rarity: string | null;
  weight: number;
  cost: number;
  is_custom: boolean;
}

// --- Magic Items -------------------------------------------------------------------

export interface MagicItemSummary {
  id: string;
  index: string | null;
  name: string;
  rarity: string;
  is_variant: boolean;
  variant_of_id: string | null;
  is_custom: boolean;
}

export interface MagicItem {
  id: string;
  index: string | null;
  name: string;
  description: string;
  equipment_category: string;
  rarity: string;
  is_custom: boolean;
  is_variant: boolean;
  variant_of_id: string | null;
  variants: MagicItemSummary[];
}

// --- Fixed vocabulary (SRD 2014 §7.4.1) — seed-only, no dedicated router yet ---

export interface AbilityScoreDefinition {
  id: string;
  index: string | null;
  is_custom: boolean;
}

export interface SkillDefinition {
  id: string;
  index: string | null;
  ability_score_id: string;
  is_custom: boolean;
}

export interface Alignment {
  id: string;
  index: string | null;
  is_custom: boolean;
}

export interface Condition {
  id: string;
  index: string | null;
  is_custom: boolean;
}

export interface DamageTypeDefinition {
  id: string;
  index: string | null;
  is_custom: boolean;
}

export interface MagicSchool {
  id: string;
  index: string | null;
  is_custom: boolean;
}

export interface Language {
  id: string;
  index: string | null;
  language_type: string;
  is_custom: boolean;
}

export interface WeaponProperty {
  id: string;
  index: string | null;
  is_custom: boolean;
}

// --- Proficiencies (SRD 2014 §7.4.3) ------------------------------------------

export interface Proficiency {
  id: string;
  index: string | null;
  proficiency_type: string;
  skill_id: string | null;
  ability_score_id: string | null;
  equipment_category_id: string | null;
  is_custom: boolean;
}

// --- Backgrounds and Feats (SRD 2014 §7.4.7) ----------------------------------

export interface BackgroundEquipment {
  id: string;
  item_id: string;
  item_name: string;
  quantity: number;
}

export interface BackgroundFeature {
  id: string;
  feature_name: string;
  description: string;
}

export interface Background {
  id: string;
  index: string | null;
  name: string;
  personality_traits: string;
  ideals: string;
  bonds: string;
  flaws: string;
  is_custom: boolean;
  proficiencies: Proficiency[];
  equipment: BackgroundEquipment[];
  feature: BackgroundFeature | null;
}

export interface BackgroundSummary {
  id: string;
  index: string | null;
  name: string;
  is_custom: boolean;
}

export interface FeatPrerequisite {
  id: string;
  ability_score_id: string | null;
  minimum_score: number;
}

export interface Feat {
  id: string;
  index: string | null;
  name: string;
  description: string;
  is_custom: boolean;
  prerequisites: FeatPrerequisite[];
}

export interface FeatSummary {
  id: string;
  index: string | null;
  name: string;
  is_custom: boolean;
}

// --- Monsters / stat blocks (SRD 2014 §7.4.8) ---------------------------------

export interface MonsterSpeed {
  walk: string | null;
  burrow: string | null;
  climb: string | null;
  fly: string | null;
  swim: string | null;
  hover: boolean;
}

export interface MonsterSense {
  passive_perception: number;
  blindsight: string | null;
  darkvision: string | null;
  tremorsense: string | null;
  truesight: string | null;
}

export interface MonsterArmorClass {
  id: string;
  ac_type: string;
  value: number;
  condition_id: string | null;
  description: string | null;
}

export interface MonsterProficiency {
  id: string;
  proficiency_id: string;
  value: number;
}

export interface MonsterDamageModifier {
  id: string;
  damage_type: string;
  modifier_type: string;
}

export interface MonsterConditionImmunity {
  id: string;
  condition: string;
}

export interface MonsterActionDamage {
  id: string;
  damage_dice: string;
  damage_type: string;
}

/** Shared shape for action, legendary action, reaction, and special ability. */
export interface MonsterAction {
  id: string;
  name: string;
  description: string;
  attack_bonus: number | null;
  save_ability_score_id: string | null;
  save_dc: number | null;
  usage_type: string | null;
  usage_times: number | null;
  damages: MonsterActionDamage[];
}

export interface Monster {
  id: string;
  index: string | null;
  name: string;
  description: string;
  size: string;
  creature_type: string;
  creature_subtype: string | null;
  alignment: string;
  hit_points: number;
  hit_dice: string;
  challenge_rating: number;
  xp: number;
  proficiency_bonus: number | null;
  languages: string;
  strength: number;
  dexterity: number;
  constitution: number;
  intelligence: number;
  wisdom: number;
  charisma: number;
  is_custom: boolean;
  speed: MonsterSpeed | null;
  senses: MonsterSense | null;
  armor_classes: MonsterArmorClass[];
  proficiencies: MonsterProficiency[];
  damage_modifiers: MonsterDamageModifier[];
  condition_immunities: MonsterConditionImmunity[];
  actions: MonsterAction[];
  legendary_actions: MonsterAction[];
  reactions: MonsterAction[];
  special_abilities: MonsterAction[];
}

export interface MonsterSummary {
  id: string;
  index: string | null;
  name: string;
  size: string;
  creature_type: string;
  challenge_rating: number;
  is_custom: boolean;
}

// --- Rules (SRD 2014 §7.4.9) ---------------------------------------------------

export interface RuleSection {
  id: string;
  index: string | null;
  name: string;
  desc: string;
  is_custom: boolean;
}

export interface Rule {
  id: string;
  index: string | null;
  name: string;
  desc: string;
  is_custom: boolean;
  sections: RuleSection[];
}

export interface RuleSummary {
  id: string;
  index: string | null;
  name: string;
  is_custom: boolean;
}

/**
 * The catalog categories with a dedicated screen in the v1 frontend
 * (PRD §6.1a). Used to type `/campaigns/[id]/catalog/[category]` routes.
 */
export type CatalogCategory =
  | "races"
  | "classes"
  | "spells"
  | "equipment"
  | "magic-items"
  | "monsters"
  | "backgrounds"
  | "feats"
  | "rules";
