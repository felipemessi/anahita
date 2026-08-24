"use client";

import { useParams } from "next/navigation";

import { useSessions } from "@/hooks/use-session";

/**
 * "The story so far": every session's `summary`, in order. Reuses
 * `useSessions` (GET /campaigns/{id}/sessions) — no dedicated backend
 * endpoint (PRD §7.10). Sessions without a summary yet are skipped.
 */
export default function RecapPage() {
  const { campaignId } = useParams<{ campaignId: string }>();
  const { data: sessions, isLoading } = useSessions(campaignId);
  const recapped = (sessions ?? [])
    .filter((session) => Boolean(session.summary))
    .sort((a, b) => a.session_number - b.session_number);

  return (
    <main className="mx-auto max-w-3xl space-y-6 px-6 py-10">
      <h1 className="text-2xl font-bold">Recap</h1>

      {isLoading ? (
        <p className="text-sm text-muted-foreground">Carregando…</p>
      ) : recapped.length > 0 ? (
        <ol className="space-y-4">
          {recapped.map((session) => (
            <li
              key={session.id}
              className="rounded-lg border border-border bg-card p-4"
            >
              <p className="font-medium">
                Sessão {session.session_number} — {session.title}
              </p>
              <p className="mt-1 whitespace-pre-wrap text-sm text-muted-foreground">
                {session.summary}
              </p>
            </li>
          ))}
        </ol>
      ) : (
        <p className="text-sm text-muted-foreground">
          Nenhum resumo de sessão ainda.
        </p>
      )}
    </main>
  );
}
