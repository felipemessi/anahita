"use client";

import { useParams } from "next/navigation";

import { useMyMembership } from "@/hooks/use-campaign";
import { useSessions } from "@/hooks/use-session";
import { NoteEditor } from "@/components/sessions/note-editor";

/**
 * There's no `GET /sessions/{id}` — the backend only exposes the list
 * endpoint (`GET /campaigns/{id}/sessions`), so the detail is derived from
 * the campaign's session list already cached by `useSessions`.
 */
export default function SessionDetailPage() {
  const { campaignId, sessionId } = useParams<{
    campaignId: string;
    sessionId: string;
  }>();
  const { data: sessions, isLoading } = useSessions(campaignId);
  const { data: membership } = useMyMembership(campaignId);
  const isDm = membership?.role === "dm";
  const session = sessions?.find((s) => s.id === sessionId);

  if (isLoading) {
    return <p className="p-6 text-sm text-muted-foreground">Carregando…</p>;
  }

  if (!session) {
    return <p className="p-6 text-sm text-muted-foreground">Sessão não encontrada.</p>;
  }

  return (
    <main className="mx-auto max-w-3xl space-y-8 px-6 py-10">
      <div>
        <h1 className="text-2xl font-bold">
          Sessão {session.session_number} — {session.title}
        </h1>
        {session.scheduled_date ? (
          <p className="text-sm text-muted-foreground">{session.scheduled_date}</p>
        ) : null}
        {session.summary ? <p className="mt-2 text-sm">{session.summary}</p> : null}
      </div>

      {isDm && session.dm_notes ? (
        <section className="rounded-lg border border-border bg-card p-4">
          <h2 className="font-semibold">Notas do DM</h2>
          <p className="mt-2 whitespace-pre-wrap text-sm text-muted-foreground">
            {session.dm_notes}
          </p>
        </section>
      ) : null}

      <NoteEditor sessionId={session.id} isDm={isDm} />
    </main>
  );
}
