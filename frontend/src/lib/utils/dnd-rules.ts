/**
 * Client-side mirror of backend/engine/abilities.py — used for instant
 * feedback in the character creation wizard and sheet before the server
 * round-trip confirms the same numbers. Keep formulas byte-for-byte
 * identical to the backend rules engine (PRD §9.3, backlog Fase 1).
 */

export const BASE_ABILITY_SCORE = 10;
export const TIER_1_PROFICIENCY_BONUS = 2;

/** Ability modifier from an ability score: `floor((score - 10) / 2)`. */
export function calculateModifier(score: number): number {
  return Math.floor((score - BASE_ABILITY_SCORE) / 2);
}

/** Proficiency bonus from total character level: `ceil(level / 4) + 1`. */
export function calculateProficiencyBonus(totalLevel: number): number {
  if (totalLevel < 1) return TIER_1_PROFICIENCY_BONUS;
  return Math.ceil(totalLevel / 4) + 1;
}

/** Total bonus for a skill, stacking proficiency and expertise. */
export function calculateSkillBonus(
  abilityMod: number,
  isProficient: boolean,
  hasExpertise: boolean,
  profBonus: number,
): number {
  let bonus = abilityMod;
  if (isProficient) {
    bonus += profBonus;
    if (hasExpertise) {
      bonus += profBonus;
    }
  }
  return bonus;
}
