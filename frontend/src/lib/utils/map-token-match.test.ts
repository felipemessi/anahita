import { describe, expect, it } from "vitest";

import { participantForToken, tokenForParticipant } from "./map-token-match";
import type { EncounterParticipant } from "@/types/combat";
import type { MapToken } from "@/types/map";

const participant: EncounterParticipant = {
  id: "p-1",
  encounter_id: "enc-1",
  character_id: "char-1",
  npc_id: null,
  monster_id: null,
  name: "Aria",
  initiative: 15,
  hit_point_max: 20,
  hit_point_current: 20,
  temporary_hit_points: 0,
  armor_class: 14,
  turn_order: 0,
  is_active: true,
  conditions: [],
  effects: [],
  concentration_dc: null,
  legendary_actions_used: 0,
  reactions_used: 0,
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

describe("participantForToken", () => {
  it("matches by shared character_id", () => {
    expect(participantForToken(token, [participant])).toEqual(participant);
  });

  it("returns null when nothing matches", () => {
    const other: MapToken = { ...token, character_id: "char-2" };
    expect(participantForToken(other, [participant])).toBeNull();
  });

  it("matches a manual token to nothing (all three keys null)", () => {
    const manual: MapToken = { ...token, character_id: null };
    expect(participantForToken(manual, [participant])).toBeNull();
  });
});

describe("tokenForParticipant", () => {
  it("matches by shared character_id", () => {
    expect(tokenForParticipant(participant, [token])).toEqual(token);
  });

  it("returns null when the participant has no token yet", () => {
    expect(tokenForParticipant({ ...participant, character_id: "char-9" }, [token])).toBeNull();
  });
});
