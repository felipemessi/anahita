import { describe, expect, it } from "vitest";

import { initialMapState, mapReducer } from "./map-provider";
import type { MapSnapshot, MapToken } from "@/types/map";

const map: MapSnapshot["map"] = {
  id: "map-1",
  session_id: "sess-1",
  name: "Old Tavern",
  url: "/files/maps/map-1.png",
  width_px: 1000,
  height_px: 800,
  grid_size_px: 50,
  created_at: "2026-01-01T00:00:00Z",
};

const token: MapToken = {
  id: "token-1",
  map_id: "map-1",
  character_id: "char-1",
  npc_id: null,
  monster_id: null,
  name: "Aria",
  x: 2,
  y: 3,
  is_visible: true,
};

const snapshot: MapSnapshot = { map, tokens: [token] };

describe("mapReducer", () => {
  it("state_sync replaces the map and tokens wholesale", () => {
    const state = mapReducer(initialMapState, {
      event_type: "state_sync",
      payload: snapshot,
    });

    expect(state.map).toEqual(map);
    expect(state.tokens).toEqual([token]);
    expect(state.lastError).toBeNull();
  });

  it("token_added appends a new token", () => {
    const synced = mapReducer(initialMapState, {
      event_type: "state_sync",
      payload: snapshot,
    });
    const newToken: MapToken = { ...token, id: "token-2", name: "Goblin" };

    const state = mapReducer(synced, { event_type: "token_added", payload: newToken });

    expect(state.tokens).toEqual([token, newToken]);
  });

  it("token_moved updates the matching token's position, leaving others untouched", () => {
    const synced = mapReducer(initialMapState, {
      event_type: "state_sync",
      payload: snapshot,
    });
    const moved: MapToken = { ...token, x: 5, y: 5 };

    const state = mapReducer(synced, { event_type: "token_moved", payload: moved });

    expect(state.tokens).toEqual([moved]);
  });

  it("token_removed drops the matching token", () => {
    const synced = mapReducer(initialMapState, {
      event_type: "state_sync",
      payload: snapshot,
    });

    const state = mapReducer(synced, {
      event_type: "token_removed",
      payload: { id: token.id },
    });

    expect(state.tokens).toEqual([]);
  });

  it("error sets lastError without discarding the map/tokens", () => {
    const synced = mapReducer(initialMapState, {
      event_type: "state_sync",
      payload: snapshot,
    });

    const state = mapReducer(synced, {
      event_type: "error",
      payload: { detail: "You can only move your own character's token" },
    });

    expect(state.lastError).toBe("You can only move your own character's token");
    expect(state.tokens).toEqual([token]);
  });
});
