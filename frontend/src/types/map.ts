/**
 * Mirrors backend/app/maps/schemas.py and domain.py (backlog Fase 15).
 */

export interface SessionMap {
  id: string;
  session_id: string;
  name: string;
  /** Resolved URL to the uploaded image (never a raw storage key). */
  url: string;
  width_px: number;
  height_px: number;
  /** Pixels per 5ft grid cell. */
  grid_size_px: number;
  created_at: string;
}

/**
 * A token is a PC, an NPC, *or* a catalog monster — never more than one.
 * None of the three set is a manual/generic token identified only by `name`.
 */
export interface MapToken {
  id: string;
  map_id: string;
  character_id: string | null;
  npc_id: string | null;
  monster_id: string | null;
  name: string;
  /** Grid cell coordinates, not pixels. */
  x: number;
  y: number;
  /** Hidden tokens are DM-only, same convention as an unrevealed NPC. */
  is_visible: boolean;
}

export interface MapTokenCreate {
  character_id?: string | null;
  npc_id?: string | null;
  monster_id?: string | null;
  name: string;
  x: number;
  y: number;
  is_visible?: boolean;
}

export interface MapSnapshot {
  map: SessionMap;
  tokens: MapToken[];
}
