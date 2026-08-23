import type { AbilityScore } from "@/types/catalog";

/** Shared in-progress state across the character creation wizard's steps. */
export interface WizardState {
  name: string;
  raceId: string;
  subraceId: string | null;
  classId: string;
  subclassId: string | null;
  backgroundId: string;
  alignment: string;
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

export const INITIAL_WIZARD_STATE: WizardState = {
  name: "",
  raceId: "",
  subraceId: null,
  classId: "",
  subclassId: null,
  backgroundId: "",
  alignment: "",
  abilityScores: { str: null, dex: null, con: null, int: null, wis: null, cha: null },
};
