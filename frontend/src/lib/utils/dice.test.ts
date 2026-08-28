import { afterEach, describe, expect, it, vi } from "vitest";

import { formatModifier, rollCheck, rollD20, rollDiceExpression } from "./dice";

describe("rollD20", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("always returns an integer between 1 and 20", () => {
    for (let i = 0; i < 200; i++) {
      const value = rollD20();
      expect(Number.isInteger(value)).toBe(true);
      expect(value).toBeGreaterThanOrEqual(1);
      expect(value).toBeLessThanOrEqual(20);
    }
  });

  it("maps Math.random 0 to 1 and just-under-1 to 20", () => {
    vi.spyOn(Math, "random").mockReturnValueOnce(0);
    expect(rollD20()).toBe(1);
    vi.spyOn(Math, "random").mockReturnValueOnce(0.9999);
    expect(rollD20()).toBe(20);
  });
});

describe("rollCheck", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("adds the modifier to the die and tags the result with the label", () => {
    vi.spyOn(Math, "random").mockReturnValue(0.5); // die = 11
    const result = rollCheck("Força", 3);
    expect(result).toEqual({ label: "Força", die: 11, modifier: 3, total: 14 });
  });

  it("supports negative modifiers", () => {
    vi.spyOn(Math, "random").mockReturnValue(0); // die = 1
    const result = rollCheck("Sabedoria", -2);
    expect(result.total).toBe(-1);
  });
});

describe("rollDiceExpression", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("rolls a single die for a bare NdM with N omitted", () => {
    vi.spyOn(Math, "random").mockReturnValue(0.9999); // 1d8 -> 8
    expect(rollDiceExpression("1d8")).toBe(8);
  });

  it("sums every die for a multi-die expression", () => {
    vi.spyOn(Math, "random").mockReturnValue(0); // each d6 -> 1
    expect(rollDiceExpression("2d6")).toBe(2);
  });

  it("returns 0 for an expression it can't parse", () => {
    expect(rollDiceExpression("not-a-dice-expression")).toBe(0);
  });
});

describe("formatModifier", () => {
  it("prefixes non-negative values with a plus sign", () => {
    expect(formatModifier(0)).toBe("+0");
    expect(formatModifier(3)).toBe("+3");
  });

  it("leaves negative values as-is", () => {
    expect(formatModifier(-2)).toBe("-2");
  });
});
