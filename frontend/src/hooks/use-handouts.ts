"use client";

import { useEffect } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { createHandout, listHandouts, revealHandout } from "@/lib/api/handouts";
import { listEncounters } from "@/lib/api/combat";
import { CombatSocket } from "@/lib/ws/combat-socket";
import type { HandoutCreateFields } from "@/types/handout";

export const HANDOUTS_QUERY_KEY = ["handouts"] as const;

/** A campaign's handouts (server-filtered: non-DM members only see revealed ones). */
export function useHandouts(campaignId: string) {
  return useQuery({
    queryKey: [...HANDOUTS_QUERY_KEY, campaignId],
    queryFn: () => listHandouts(campaignId),
    enabled: Boolean(campaignId),
  });
}

/** Create a handout, optionally with a file upload (DM only). */
export function useCreateHandout(campaignId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      fields,
      file,
    }: {
      fields: HandoutCreateFields;
      file?: File | null;
    }) => createHandout(campaignId, fields, file),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: [...HANDOUTS_QUERY_KEY, campaignId],
      });
    },
  });
}

/** Reveal a handout (DM only); invalidates the campaign's handout list. */
export function useRevealHandout(campaignId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (handoutId: string) => revealHandout(handoutId),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: [...HANDOUTS_QUERY_KEY, campaignId],
      });
    },
  });
}

/**
 * While `sessionId` has an active encounter, listens on its combat
 * WebSocket for `handout_revealed` (PRD §10.3) and refetches the handout
 * list so a player sees a reveal without reloading — reusing `lib/ws`
 * rather than opening a second kind of socket.
 */
export function useHandoutRevealListener(
  campaignId: string,
  sessionId: string | null,
): void {
  const queryClient = useQueryClient();
  const { data: encounters } = useQuery({
    queryKey: ["encounters", sessionId],
    queryFn: () => listEncounters(sessionId ?? ""),
    enabled: Boolean(sessionId),
  });
  const activeEncounterId = encounters?.find((e) => e.status === "active")?.id ?? null;

  useEffect(() => {
    if (!activeEncounterId) return;

    const socket = new CombatSocket(activeEncounterId, {
      onEvent: (event) => {
        if (event.event_type === "handout_revealed") {
          void queryClient.invalidateQueries({
            queryKey: [...HANDOUTS_QUERY_KEY, campaignId],
          });
        }
      },
    });
    socket.connect();

    return () => socket.close();
  }, [activeEncounterId, campaignId, queryClient]);
}
