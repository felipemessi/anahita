"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  addNote,
  completeSession,
  createSession,
  listNotes,
  listSessions,
  openSession,
  updateSession,
} from "@/lib/api/sessions";
import type { SessionCreate, SessionNoteCreate, SessionUpdate } from "@/types/session";

export const SESSIONS_QUERY_KEY = ["sessions"] as const;

/** A campaign's sessions, in order. */
export function useSessions(campaignId: string) {
  return useQuery({
    queryKey: [...SESSIONS_QUERY_KEY, campaignId],
    queryFn: () => listSessions(campaignId),
    enabled: Boolean(campaignId),
  });
}

/** Create a session (DM only); invalidates the campaign's session list on success. */
export function useCreateSession(campaignId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: SessionCreate) => createSession(campaignId, data),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: [...SESSIONS_QUERY_KEY, campaignId],
      });
    },
  });
}

/** A session's notes; the DM sees private notes, other members don't (server-filtered). */
export function useSessionNotes(sessionId: string) {
  return useQuery({
    queryKey: [...SESSIONS_QUERY_KEY, sessionId, "notes"],
    queryFn: () => listNotes(sessionId),
    enabled: Boolean(sessionId),
  });
}

/** Add a note to a session; invalidates that session's note list on success. */
export function useAddNote(sessionId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: SessionNoteCreate) => addNote(sessionId, data),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: [...SESSIONS_QUERY_KEY, sessionId, "notes"],
      });
    },
  });
}

/** Open a planned session for play (DM only); invalidates the campaign's session list. */
export function useOpenSession(campaignId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (sessionId: string) => openSession(sessionId),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: [...SESSIONS_QUERY_KEY, campaignId],
      });
    },
  });
}

/** Complete an in-progress session (DM only); invalidates the campaign's session list. */
export function useCompleteSession(campaignId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (sessionId: string) => completeSession(sessionId),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: [...SESSIONS_QUERY_KEY, campaignId],
      });
    },
  });
}

/** Edit a session's title/scheduled date (DM only); invalidates the campaign's session list. */
export function useUpdateSession(campaignId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ sessionId, data }: { sessionId: string; data: SessionUpdate }) =>
      updateSession(sessionId, data),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: [...SESSIONS_QUERY_KEY, campaignId],
      });
    },
  });
}
