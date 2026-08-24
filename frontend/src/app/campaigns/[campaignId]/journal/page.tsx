"use client";

import { useParams } from "next/navigation";

import { JournalEditor } from "@/components/journal/journal-editor";
import { JournalEntryCard } from "@/components/journal/journal-entry-card";
import { useJournalEntries } from "@/hooks/use-journal";

/**
 * DM-only campaign journal. The route stays out of the nav for non-DM
 * members (see campaign-sidebar.tsx), but the backend also rejects the
 * request with a 403 either way — this page handles that case without
 * ever rendering the editor or leaking whether entries exist.
 */
export default function JournalPage() {
  const { campaignId } = useParams<{ campaignId: string }>();
  const { data: entries, isLoading, isError } = useJournalEntries(campaignId);

  if (isError) {
    return (
      <main className="mx-auto max-w-3xl px-6 py-10">
        <p className="text-sm text-muted-foreground">
          Você não tem acesso a esta página.
        </p>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-3xl space-y-6 px-6 py-10">
      <h1 className="text-2xl font-bold">Diário</h1>

      <JournalEditor campaignId={campaignId} />

      {isLoading ? (
        <p className="text-sm text-muted-foreground">Carregando…</p>
      ) : entries && entries.length > 0 ? (
        <ul className="space-y-2">
          {entries.map((entry) => (
            <li key={entry.id}>
              <JournalEntryCard campaignId={campaignId} entry={entry} />
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-sm text-muted-foreground">Nenhuma entrada ainda.</p>
      )}
    </main>
  );
}
