import { apiFetch } from "@/lib/api/client";
import type { JournalEntry, JournalEntryCreate, JournalEntryUpdate } from "@/types/journal";

/** Calls the journal endpoints exposed by backend/app/journal/router.py. All DM-only. */

/** List a campaign's journal entries, most recent first. DM-only. */
export function listJournalEntries(campaignId: string): Promise<JournalEntry[]> {
  return apiFetch<JournalEntry[]>(`/campaigns/${campaignId}/journal`);
}

/** Create a journal entry. DM-only. */
export function createJournalEntry(
  campaignId: string,
  data: JournalEntryCreate,
): Promise<JournalEntry> {
  return apiFetch<JournalEntry>(`/campaigns/${campaignId}/journal`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/** Update a journal entry's title/content/session link. DM-only. */
export function updateJournalEntry(
  entryId: string,
  data: JournalEntryUpdate,
): Promise<JournalEntry> {
  return apiFetch<JournalEntry>(`/journal/${entryId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

/** Delete a journal entry. DM-only. */
export function deleteJournalEntry(entryId: string): Promise<void> {
  return apiFetch<void>(`/journal/${entryId}`, { method: "DELETE" });
}
