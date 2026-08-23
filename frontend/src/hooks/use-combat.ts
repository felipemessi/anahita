"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { createEncounter, listEncounters, startEncounter } from "@/lib/api/combat";
import { useCombatContext } from "@/providers/combat-provider";
import type {
  Condition,
  EncounterCreate,
  EncounterParticipantCreate,
} from "@/types/combat";

export const ENCOUNTERS_QUERY_KEY = ["encounters"] as const;

/** A session's encounters (REST — entry point into the live tracker). */
export function useEncounters(sessionId: string) {
  return useQuery({
    queryKey: [...ENCOUNTERS_QUERY_KEY, sessionId],
    queryFn: () => listEncounters(sessionId),
    enabled: Boolean(sessionId),
  });
}

/** Create an encounter for a session (DM only); invalidates its encounter list. */
export function useCreateEncounter(sessionId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: EncounterCreate) => createEncounter(sessionId, data),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: [...ENCOUNTERS_QUERY_KEY, sessionId],
      });
    },
  });
}

/** Start a preparing encounter (DM only) — after this the WS accepts turn commands. */
export function useStartEncounter() {
  return useMutation({
    mutationFn: (encounterId: string) => startEncounter(encounterId),
  });
}

/**
 * The current encounter (kept in sync by `CombatProvider` over the
 * WebSocket) plus command senders for the DM-only actions. Non-DM callers
 * should simply not invoke the senders — the server rejects them anyway
 * (`ws_router._handle_message`), but the read-only player view (história 4)
 * hides the controls that would call them.
 */
export function useCombat() {
  const { encounter, lastError, isConnected, sendCommand } = useCombatContext();

  function advanceTurn(): void {
    sendCommand({ event_type: "advance_turn" });
  }

  function updateParticipant(
    participantId: string,
    changes: {
      hitPointCurrent?: number;
      temporaryHitPoints?: number;
      armorClass?: number;
      addCondition?: Condition;
      removeCondition?: Condition;
    },
  ): void {
    sendCommand({
      event_type: "update_participant",
      payload: {
        participant_id: participantId,
        hit_point_current: changes.hitPointCurrent,
        temporary_hit_points: changes.temporaryHitPoints,
        armor_class: changes.armorClass,
        add_condition: changes.addCondition,
        remove_condition: changes.removeCondition,
      },
    });
  }

  function addParticipant(data: EncounterParticipantCreate): void {
    sendCommand({ event_type: "add_participant", payload: data });
  }

  function removeParticipant(participantId: string): void {
    sendCommand({
      event_type: "remove_participant",
      payload: { participant_id: participantId },
    });
  }

  function endEncounter(): void {
    sendCommand({ event_type: "end_encounter" });
  }

  return {
    encounter,
    lastError,
    isConnected,
    advanceTurn,
    updateParticipant,
    addParticipant,
    removeParticipant,
    endEncounter,
  };
}
