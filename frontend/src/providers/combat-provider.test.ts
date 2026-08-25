import { describe, expect, it } from "vitest";

import { combatReducer, initialCombatState } from "./combat-provider";
import type { Encounter, EncounterParticipant } from "@/types/combat";

const encounter: Encounter = {
  id: "enc-1",
  session_id: "sess-1",
  name: "Emboscada na estrada",
  status: "active",
  current_round: 1,
  current_turn_order: 0,
  created_at: "2026-01-01T00:00:00Z",
  participants: [
    {
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
    },
    {
      id: "p-2",
      encounter_id: "enc-1",
      character_id: null,
      npc_id: null,
      monster_id: null,
      name: "Goblin",
      initiative: 10,
      hit_point_max: 7,
      hit_point_current: 7,
      temporary_hit_points: 0,
      armor_class: 13,
      turn_order: 1,
      is_active: true,
      conditions: [],
      effects: [],
    },
  ],
};

describe("combatReducer", () => {
  it("state_sync replaces the encounter wholesale", () => {
    const state = combatReducer(initialCombatState, {
      event_type: "state_sync",
      payload: encounter,
    });

    expect(state.encounter).toEqual(encounter);
    expect(state.lastError).toBeNull();
  });

  it("turn_advanced updates round/turn_order without touching participants", () => {
    const synced = combatReducer(initialCombatState, {
      event_type: "state_sync",
      payload: encounter,
    });

    const state = combatReducer(synced, {
      event_type: "turn_advanced",
      payload: { round: 2, turn_order: 1, participant_id: "p-2" },
    });

    expect(state.encounter?.current_round).toBe(2);
    expect(state.encounter?.current_turn_order).toBe(1);
    expect(state.encounter?.participants).toEqual(encounter.participants);
  });

  it("participant_updated merges the updated participant by id, leaving others untouched", () => {
    const synced = combatReducer(initialCombatState, {
      event_type: "state_sync",
      payload: encounter,
    });

    const original = encounter.participants[0];
    if (!original) throw new Error("fixture missing participant 0");
    const damaged: EncounterParticipant = { ...original, hit_point_current: 8 };
    const state = combatReducer(synced, {
      event_type: "participant_updated",
      payload: damaged,
    });

    expect(state.encounter?.participants).toEqual([
      damaged,
      encounter.participants[1],
    ]);
  });

  it("encounter_status_changed updates the encounter's status", () => {
    const synced = combatReducer(initialCombatState, {
      event_type: "state_sync",
      payload: encounter,
    });

    const state = combatReducer(synced, {
      event_type: "encounter_status_changed",
      payload: { status: "completed" },
    });

    expect(state.encounter?.status).toBe("completed");
  });

  it("ignores turn_advanced/participant_updated/encounter_status_changed before any state_sync", () => {
    const state = combatReducer(initialCombatState, {
      event_type: "turn_advanced",
      payload: { round: 2, turn_order: 1, participant_id: "p-2" },
    });

    expect(state).toBe(initialCombatState);
  });

  it("error sets lastError without discarding the encounter", () => {
    const synced = combatReducer(initialCombatState, {
      event_type: "state_sync",
      payload: encounter,
    });

    const state = combatReducer(synced, {
      event_type: "error",
      payload: { detail: "Only the DM can send commands" },
    });

    expect(state.lastError).toBe("Only the DM can send commands");
    expect(state.encounter).toEqual(encounter);
  });
});
