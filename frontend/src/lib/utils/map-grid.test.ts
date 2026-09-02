import { describe, expect, it } from "vitest";

import {
  cellDistance,
  cellsInRadius,
  clampCell,
  feetToCells,
  pixelToCell,
} from "./map-grid";

describe("feetToCells", () => {
  it("converts at 5ft per cell, rounding down", () => {
    expect(feetToCells(30)).toBe(6);
    expect(feetToCells(25)).toBe(5);
    expect(feetToCells(7)).toBe(1);
  });
});

describe("cellDistance", () => {
  it("is Chebyshev — diagonal costs the same as orthogonal", () => {
    expect(cellDistance(0, 0, 3, 0)).toBe(3);
    expect(cellDistance(0, 0, 0, 4)).toBe(4);
    expect(cellDistance(0, 0, 3, 3)).toBe(3);
    expect(cellDistance(2, 2, 2, 2)).toBe(0);
  });
});

describe("pixelToCell", () => {
  it("floors pixel offsets into whole grid cells", () => {
    expect(pixelToCell(0, 0, 50)).toEqual({ x: 0, y: 0 });
    expect(pixelToCell(49, 99, 50)).toEqual({ x: 0, y: 1 });
    expect(pixelToCell(150, 50, 50)).toEqual({ x: 3, y: 1 });
  });
});

describe("clampCell", () => {
  it("clamps to the map's bounds", () => {
    expect(clampCell({ x: -1, y: -5 }, 500, 500, 50)).toEqual({ x: 0, y: 0 });
    expect(clampCell({ x: 100, y: 100 }, 500, 500, 50)).toEqual({ x: 9, y: 9 });
    expect(clampCell({ x: 3, y: 4 }, 500, 500, 50)).toEqual({ x: 3, y: 4 });
  });
});

describe("cellsInRadius", () => {
  it("returns a (2r+1)^2-bounded diamond... actually square, per Chebyshev", () => {
    const cells = cellsInRadius(0, 0, 1);
    expect(cells).toHaveLength(9); // 3x3 square around the origin
    expect(cells).toContainEqual({ x: 1, y: 1 });
    expect(cells).toContainEqual({ x: -1, y: -1 });
  });

  it("offsets by the origin cell", () => {
    const cells = cellsInRadius(5, 5, 0);
    expect(cells).toEqual([{ x: 5, y: 5 }]);
  });
});
