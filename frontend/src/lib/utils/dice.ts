/**
 * Client-side dice rolling for the character sheet's quick-roll interactions
 * (ability checks, saving throws, skills — PRD frontend backlog Fase 5).
 * Purely cosmetic: nothing here is persisted or shared with other players.
 */

/** Roll a single d20 (1-20 inclusive). */
export function rollD20(): number {
  return Math.floor(Math.random() * 20) + 1;
}

/** Roll a single d6 (1-6 inclusive). */
export function rollD6(): number {
  return Math.floor(Math.random() * 6) + 1;
}

/**
 * Roll a `NdM` dice expression (e.g. `"1d8"`, `"2d6"`) and return the sum of
 * the dice, no modifier — matches `WeaponDetail.damage_dice`'s format. An
 * expression that doesn't parse rolls as 0 rather than throwing, since this
 * only ever runs after a modal is already open.
 */
export function rollDiceExpression(expression: string): number {
  const match = /^(\d*)d(\d+)$/i.exec(expression.trim());
  if (!match) return 0;
  const count = match[1] ? Number(match[1]) : 1;
  const sides = Number(match[2]);
  let total = 0;
  for (let i = 0; i < count; i++) {
    total += Math.floor(Math.random() * sides) + 1;
  }
  return total;
}

/** Roll 4d6 and drop the lowest die — the PHB's "roll" ability score method. */
export function roll4d6DropLowest(): number {
  const dice = [rollD6(), rollD6(), rollD6(), rollD6()].sort((a, b) => a - b);
  return dice[1]! + dice[2]! + dice[3]!;
}

export interface DiceRollResult {
  /** Human-readable label for what was rolled, e.g. "Força" or "Furtividade". */
  label: string;
  /** The raw d20 face. */
  die: number;
  /** The modifier/bonus added to the die. */
  modifier: number;
  /** `die + modifier`. */
  total: number;
}

/** Roll 1d20 and add `modifier`, tagging the result with `label`. */
export function rollCheck(label: string, modifier: number): DiceRollResult {
  const die = rollD20();
  return { label, die, modifier, total: die + modifier };
}

/** Format a modifier/bonus with an explicit sign, e.g. `3` -> "+3", `-1` -> "-1". */
export function formatModifier(value: number): string {
  return value >= 0 ? `+${value}` : `${value}`;
}
