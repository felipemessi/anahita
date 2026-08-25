"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { createEncounter, listEncounters, startEncounter } from "@/lib/api/combat";
import type { WSDeclareActionPayload } from "@/lib/ws/types";
import { useCombatContext } from "@/providers/combat-provider";
import type {
  CombatActionType,
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
  const { encounter, lastError, actionLog, isConnected, sendCommand } = useCombatContext();

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

  /**
   * Roll initiative for `participantId` — a player only for their own
   * character's participant, the DM for any (server-enforced). Omitting
   * `initiative` rolls `1d20 + DEX` server-side; passing it uses that value
   * as a manual roll instead (backlog Fase 6 história 6).
   */
  function rollInitiative(participantId: string, initiative?: number): void {
    sendCommand({
      event_type: "roll_initiative",
      payload: { participant_id: participantId, initiative },
    });
  }

  /**
   * Declare a combat action (attack/grapple/shove) — same ownership rule as
   * `rollInitiative`. See `WSDeclareActionPayload` for the full field docs.
   */
  function declareAction(
    data: Omit<WSDeclareActionPayload, "action_type"> & {
      actionType: CombatActionType;
    },
  ): void {
    const { actionType, ...rest } = data;
    sendCommand({
      event_type: "declare_action",
      payload: { ...rest, action_type: actionType },
    });
  }

  /**
   * Use a monster/NPC's legendary action (Fase 7). DM only — rejected
   * server-side outside an NPC/monster participant, on its own turn, or
   * past its per-round budget. Named `sendLegendaryAction` (not
   * `useLegendaryAction`) despite the domain term, so a caller
   * destructuring it doesn't read as a React hook.
   */
  function sendLegendaryAction(
    participantId: string,
    targetId: string,
    legendaryActionId: string,
  ): void {
    sendCommand({
      event_type: "use_legendary_action",
      payload: {
        participant_id: participantId,
        target_id: targetId,
        legendary_action_id: legendaryActionId,
      },
    });
  }

  /**
   * Trigger a monster/NPC's reaction (Fase 7). DM only — once per round,
   * server-enforced.
   */
  function triggerReaction(
    participantId: string,
    targetId: string,
    reactionId: string,
  ): void {
    sendCommand({
      event_type: "trigger_reaction",
      payload: {
        participant_id: participantId,
        target_id: targetId,
        reaction_id: reactionId,
      },
    });
  }

  return {
    encounter,
    lastError,
    actionLog,
    isConnected,
    advanceTurn,
    updateParticipant,
    addParticipant,
    removeParticipant,
    endEncounter,
    rollInitiative,
    declareAction,
    sendLegendaryAction,
    triggerReaction,
  };
}
