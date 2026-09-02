/**
 * Pure grid-geometry helpers for `components/maps/map-canvas.tsx` — kept
 * separate from the component for unit testing without mounting/simulating
 * pointer events. Mirrors backend/app/maps/domain.py's conventions
 * (5ft/cell, Chebyshev distance) so client-side range highlighting agrees
 * with what the server actually enforces.
 */

/** Feet per grid cell — mirrors `app.maps.domain.FEET_PER_CELL`. */
export const FEET_PER_CELL = 5;

/** A character's speed (feet) to a whole number of grid cells, rounded down. */
export function feetToCells(feet: number): number {
  return Math.floor(feet / FEET_PER_CELL);
}

/**
 * Chebyshev distance between two grid cells — every neighbor, diagonal
 * included, costs one cell. Mirrors `app.maps.domain.cell_distance`.
 */
export function cellDistance(x1: number, y1: number, x2: number, y2: number): number {
  return Math.max(Math.abs(x2 - x1), Math.abs(y2 - y1));
}

/**
 * Convert a pointer position (in px, relative to the *unscaled* map's
 * top-left corner — i.e. already divided by the current zoom `scale`) to
 * the grid cell it falls in.
 */
export function pixelToCell(
  offsetX: number,
  offsetY: number,
  gridSizePx: number,
): { x: number; y: number } {
  return { x: Math.floor(offsetX / gridSizePx), y: Math.floor(offsetY / gridSizePx) };
}

/** Clamp a cell coordinate to stay within a map's bounds (0-indexed, inclusive). */
export function clampCell(
  cell: { x: number; y: number },
  widthPx: number,
  heightPx: number,
  gridSizePx: number,
): { x: number; y: number } {
  const maxX = Math.max(0, Math.ceil(widthPx / gridSizePx) - 1);
  const maxY = Math.max(0, Math.ceil(heightPx / gridSizePx) - 1);
  return {
    x: Math.min(Math.max(cell.x, 0), maxX),
    y: Math.min(Math.max(cell.y, 0), maxY),
  };
}

/** All cells within `radiusCells` of `(originX, originY)`, Chebyshev distance. */
export function cellsInRadius(
  originX: number,
  originY: number,
  radiusCells: number,
): { x: number; y: number }[] {
  const cells: { x: number; y: number }[] = [];
  for (let dx = -radiusCells; dx <= radiusCells; dx++) {
    for (let dy = -radiusCells; dy <= radiusCells; dy++) {
      if (cellDistance(0, 0, dx, dy) <= radiusCells) {
        cells.push({ x: originX + dx, y: originY + dy });
      }
    }
  }
  return cells;
}
