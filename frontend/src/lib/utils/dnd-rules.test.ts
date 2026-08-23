import { describe, expect, it } from "vitest";

import { calculateModifier, calculateProficiencyBonus, calculateSkillBonus } from "./dnd-rules";

// Same cases as backend/tests/engine/test_abilities.py, kept in sync so the
// client-side mirror never drifts from the rules engine.

describe("calculateModifier", () => {
  it("computes floor((score - 10) / 2)", () => {
    expect(calculateModifier(10)).toBe(0);
    expect(calculateModifier(11)).toBe(0);
    expect(calculateModifier(12)).toBe(1);
    expect(calculateModifier(13)).toBe(1);
    expect(calculateModifier(8)).toBe(-1);
    expect(calculateModifier(9)).toBe(-1);
    expect(calculateModifier(20)).toBe(5);
  });
});

describe("calculateProficiencyBonus", () => {
  it("matches the standard 5e level breakpoints", () => {
    expect(calculateProficiencyBonus(1)).toBe(2);
    expect(calculateProficiencyBonus(4)).toBe(2);
    expect(calculateProficiencyBonus(5)).toBe(3);
    expect(calculateProficiencyBonus(9)).toBe(4);
    expect(calculateProficiencyBonus(13)).toBe(5);
    expect(calculateProficiencyBonus(17)).toBe(6);
    expect(calculateProficiencyBonus(20)).toBe(6);
  });
});

describe("calculateSkillBonus", () => {
  it("stacks proficiency and expertise correctly", () => {
    const mod = 3;
    const prof = 3;

    expect(calculateSkillBonus(mod, false, false, prof)).toBe(3);
    expect(calculateSkillBonus(mod, true, false, prof)).toBe(6);
    expect(calculateSkillBonus(mod, true, true, prof)).toBe(9);
  });
});
