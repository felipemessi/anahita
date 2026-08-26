import type { AbilityScore } from "@/types/catalog";
import type { AbilityGenerationMethod } from "@/types/character";

/** Shared in-progress state across the character creation wizard's steps. */
export interface WizardState {
  name: string;
  raceId: string;
  subraceId: string | null;
  classId: string;
  subclassId: string | null;
  backgroundId: string;
  alignment: string;
  abilityGenerationMethod: AbilityGenerationMethod;
  abilityScores: Record<AbilityScore, number | null>;
}

export const ABILITY_ORDER: AbilityScore[] = ["str", "dex", "con", "int", "wis", "cha"];

export const ABILITY_LABELS: Record<AbilityScore, string> = {
  str: "Força",
  dex: "Destreza",
  con: "Constituição",
  int: "Inteligência",
  wis: "Sabedoria",
  cha: "Carisma",
};

/** PHB standard array — assigned by the player across the 6 abilities. */
export const STANDARD_ARRAY = [15, 14, 13, 12, 10, 8];

/** PHB point-buy cost table (base score -> point cost), scores 8-15 only. */
export const POINT_BUY_COSTS: Record<number, number> = {
  8: 0,
  9: 1,
  10: 2,
  11: 3,
  12: 4,
  13: 5,
  14: 7,
  15: 9,
};
export const POINT_BUY_BUDGET = 27;
export const POINT_BUY_MIN = 8;
export const POINT_BUY_MAX = 15;

export const INITIAL_WIZARD_STATE: WizardState = {
  name: "",
  raceId: "",
  subraceId: null,
  classId: "",
  subclassId: null,
  backgroundId: "",
  alignment: "",
  abilityGenerationMethod: "standard_array",
  abilityScores: { str: null, dex: null, con: null, int: null, wis: null, cha: null },
};
