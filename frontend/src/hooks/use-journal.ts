"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  createJournalEntry,
  deleteJournalEntry,
  listJournalEntries,
  updateJournalEntry,
} from "@/lib/api/journal";
import type { JournalEntryCreate, JournalEntryUpdate } from "@/types/journal";

export const JOURNAL_QUERY_KEY = ["journal"] as const;

/** A campaign's journal entries, most recent first. DM-only — 403s for players. */
export function useJournalEntries(campaignId: string) {
  return useQuery({
    queryKey: [...JOURNAL_QUERY_KEY, campaignId],
    queryFn: () => listJournalEntries(campaignId),
    enabled: Boolean(campaignId),
    retry: false,
  });
}

/** Create a journal entry (DM only); invalidates the campaign's entry list. */
export function useCreateJournalEntry(campaignId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: JournalEntryCreate) => createJournalEntry(campaignId, data),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: [...JOURNAL_QUERY_KEY, campaignId],
      });
    },
  });
}

/** Update a journal entry (DM only); invalidates the campaign's entry list. */
export function useUpdateJournalEntry(campaignId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ entryId, data }: { entryId: string; data: JournalEntryUpdate }) =>
      updateJournalEntry(entryId, data),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: [...JOURNAL_QUERY_KEY, campaignId],
      });
    },
  });
}

/** Delete a journal entry (DM only); invalidates the campaign's entry list. */
export function useDeleteJournalEntry(campaignId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (entryId: string) => deleteJournalEntry(entryId),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: [...JOURNAL_QUERY_KEY, campaignId],
      });
    },
  });
}
