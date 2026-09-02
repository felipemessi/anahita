"use client";

import { useRef, useState } from "react";

import { CharacterAvatar } from "@/components/characters/character-avatar";
import { cellDistance, clampCell, pixelToCell } from "@/lib/utils/map-grid";
import type { MapToken, SessionMap } from "@/types/map";

const MIN_SCALE = 0.25;
const MAX_SCALE = 3;
const ZOOM_STEP = 0.1;
/** Below this pointer travel (px, viewport space) a drag is treated as a click. */
const CLICK_THRESHOLD_PX = 5;

export interface MovementRange {
  originX: number;
  originY: number;
  radiusCells: number;
}

/**
 * Battle map view (backlog Fase 15): pans/zooms over the map image with a
 * grid overlay, positions tokens by cell, and supports drag-and-drop
 * (snapped to the nearest cell) or click-to-select depending on the props
 * passed in.
 *
 * Implemented as absolutely-positioned DOM elements over a background
 * image (not a literal `<canvas>` 2D-context surface) — a deliberate
 * choice: it lets tokens reuse `CharacterAvatar` directly (its own
 * docstring anticipates this), and makes drag-and-drop/pan/zoom testable
 * with ordinary DOM pointer events instead of canvas-coordinate math.
 */
export function MapCanvas({
  map,
  tokens,
  isDm = false,
  onMoveToken,
  canMoveToken,
  resolveTokenDisplay,
  movementRange,
  selectedTokenIds,
  onToggleTokenSelect,
}: {
  map: SessionMap;
  tokens: MapToken[];
  /** Hidden (`is_visible: false`) tokens are only rendered for the DM. */
  isDm?: boolean;
  /** Called with the snapped `(x, y)` cell after a successful drag. */
  onMoveToken?: (tokenId: string, x: number, y: number) => void;
  /**
   * Whether the current viewer may attempt to drag this token — defaults to
   * always allowing the attempt; the server is the actual authority
   * (`MapService.update_token_position`, 403/422 on rejection surfaced via
   * `lastError`), same "client doesn't gate, server enforces" convention
   * `ActionPicker` already uses for declaring combat actions.
   */
  canMoveToken?: (token: MapToken) => boolean;
  resolveTokenDisplay?: (token: MapToken) => { name: string; portraitUrl: string | null };
  /** Cells reachable within the current turn's remaining speed — highlighted (Fase 15 história 3). */
  movementRange?: MovementRange | null;
  /** Fase 15 história 5 — clicking a token toggles it in/out of the target selection instead of dragging. */
  selectedTokenIds?: string[];
  onToggleTokenSelect?: (tokenId: string) => void;
}) {
  const viewportRef = useRef<HTMLDivElement>(null);
  const [transform, setTransform] = useState({ scale: 1, offsetX: 0, offsetY: 0 });
  const [panStart, setPanStart] = useState<{ x: number; y: number } | null>(null);
  const [drag, setDrag] = useState<{
    tokenId: string;
    startClientX: number;
    startClientY: number;
    dx: number;
    dy: number;
  } | null>(null);

  const cellPx = map.grid_size_px;

  function handleWheel(event: React.WheelEvent<HTMLDivElement>) {
    event.preventDefault();
    const delta = event.deltaY < 0 ? ZOOM_STEP : -ZOOM_STEP;
    setTransform((t) => ({
      ...t,
      scale: Math.min(MAX_SCALE, Math.max(MIN_SCALE, t.scale + delta)),
    }));
  }

  function handleBackgroundPointerDown(event: React.PointerEvent<HTMLDivElement>) {
    if (event.target !== event.currentTarget) return;
    setPanStart({ x: event.clientX - transform.offsetX, y: event.clientY - transform.offsetY });
  }

  function handleBackgroundPointerMove(event: React.PointerEvent<HTMLDivElement>) {
    if (!panStart) return;
    setTransform((t) => ({
      ...t,
      offsetX: event.clientX - panStart.x,
      offsetY: event.clientY - panStart.y,
    }));
  }

  function endPan() {
    setPanStart(null);
  }

  function handleTokenPointerDown(
    token: MapToken,
    event: React.PointerEvent<HTMLDivElement>,
  ) {
    event.stopPropagation();
    setDrag({
      tokenId: token.id,
      startClientX: event.clientX,
      startClientY: event.clientY,
      dx: 0,
      dy: 0,
    });
  }

  function handleTokenPointerMove(event: React.PointerEvent<HTMLDivElement>) {
    if (!drag) return;
    event.stopPropagation();
    setDrag({
      ...drag,
      dx: event.clientX - drag.startClientX,
      dy: event.clientY - drag.startClientY,
    });
  }

  function handleTokenPointerUp(token: MapToken, event: React.PointerEvent<HTMLDivElement>) {
    event.stopPropagation();
    const activeDrag = drag;
    setDrag(null);
    if (!activeDrag || activeDrag.tokenId !== token.id) return;

    const traveled = Math.hypot(activeDrag.dx, activeDrag.dy);
    if (traveled < CLICK_THRESHOLD_PX) {
      onToggleTokenSelect?.(token.id);
      return;
    }

    const allowed = canMoveToken ? canMoveToken(token) : true;
    if (!allowed || !onMoveToken) return;
    const viewport = viewportRef.current;
    if (!viewport) return;
    const rect = viewport.getBoundingClientRect();
    const mapOffsetX = (event.clientX - rect.left - transform.offsetX) / transform.scale;
    const mapOffsetY = (event.clientY - rect.top - transform.offsetY) / transform.scale;
    const cell = clampCell(
      pixelToCell(mapOffsetX, mapOffsetY, cellPx),
      map.width_px,
      map.height_px,
      cellPx,
    );
    onMoveToken(token.id, cell.x, cell.y);
  }

  return (
    <div
      ref={viewportRef}
      role="application"
      aria-label={`Mapa: ${map.name}`}
      onWheel={handleWheel}
      onPointerDown={handleBackgroundPointerDown}
      onPointerMove={handleBackgroundPointerMove}
      onPointerUp={endPan}
      onPointerLeave={endPan}
      className="relative h-[500px] w-full touch-none overflow-hidden rounded-lg border border-border bg-muted"
    >
      <div
        data-testid="map-surface"
        style={{
          position: "absolute",
          left: 0,
          top: 0,
          width: map.width_px,
          height: map.height_px,
          transform: `translate(${transform.offsetX}px, ${transform.offsetY}px) scale(${transform.scale})`,
          transformOrigin: "top left",
          backgroundImage: `url(${map.url})`,
          backgroundSize: "cover",
        }}
      >
        <div
          aria-hidden
          style={{
            position: "absolute",
            inset: 0,
            backgroundImage:
              "linear-gradient(to right, rgba(0,0,0,0.15) 1px, transparent 1px)," +
              "linear-gradient(to bottom, rgba(0,0,0,0.15) 1px, transparent 1px)",
            backgroundSize: `${cellPx}px ${cellPx}px`,
          }}
        />

        {movementRange ? (
          <MovementRangeOverlay range={movementRange} cellPx={cellPx} map={map} />
        ) : null}

        {tokens.map((token) => {
          if (!token.is_visible && !isDm) return null;
          const display = resolveTokenDisplay?.(token) ?? { name: token.name, portraitUrl: null };
          const isDragging = drag?.tokenId === token.id;
          const isSelected = selectedTokenIds?.includes(token.id) ?? false;
          return (
            <div
              key={token.id}
              role="button"
              tabIndex={0}
              aria-label={`Token: ${display.name}`}
              aria-pressed={isSelected}
              onPointerDown={(e) => handleTokenPointerDown(token, e)}
              onPointerMove={handleTokenPointerMove}
              onPointerUp={(e) => handleTokenPointerUp(token, e)}
              style={{
                position: "absolute",
                left: token.x * cellPx,
                top: token.y * cellPx,
                width: cellPx,
                height: cellPx,
                transform: isDragging ? `translate(${drag.dx}px, ${drag.dy}px)` : undefined,
                cursor: canMoveToken?.(token) ? "grab" : onToggleTokenSelect ? "pointer" : "default",
                outline: isSelected ? "3px solid var(--primary, #6366f1)" : undefined,
                outlineOffset: -3,
                opacity: token.is_visible ? 1 : 0.5,
              }}
            >
              <CharacterAvatar
                name={display.name}
                portraitUrl={display.portraitUrl}
                size={cellPx}
              />
            </div>
          );
        })}
      </div>
    </div>
  );
}

function MovementRangeOverlay({
  range,
  cellPx,
  map,
}: {
  range: MovementRange;
  cellPx: number;
  map: SessionMap;
}) {
  const maxCols = Math.ceil(map.width_px / cellPx);
  const maxRows = Math.ceil(map.height_px / cellPx);
  const minX = Math.max(0, range.originX - range.radiusCells);
  const maxX = Math.min(maxCols - 1, range.originX + range.radiusCells);
  const minY = Math.max(0, range.originY - range.radiusCells);
  const maxY = Math.min(maxRows - 1, range.originY + range.radiusCells);

  const cells: { x: number; y: number }[] = [];
  for (let x = minX; x <= maxX; x++) {
    for (let y = minY; y <= maxY; y++) {
      if (cellDistance(range.originX, range.originY, x, y) <= range.radiusCells) {
        cells.push({ x, y });
      }
    }
  }

  return (
    <>
      {cells.map((cell) => (
        <div
          key={`${cell.x}-${cell.y}`}
          aria-hidden
          data-testid="movement-range-cell"
          style={{
            position: "absolute",
            left: cell.x * cellPx,
            top: cell.y * cellPx,
            width: cellPx,
            height: cellPx,
            backgroundColor: "rgba(16, 185, 129, 0.2)",
            pointerEvents: "none",
          }}
        />
      ))}
    </>
  );
}
