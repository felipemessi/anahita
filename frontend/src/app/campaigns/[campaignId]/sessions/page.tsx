"use client";

import { useState } from "react";
import { useParams } from "next/navigation";

import { useMyMembership } from "@/hooks/use-campaign";
import { useCreateSession, useSessions } from "@/hooks/use-session";
import { SessionCard } from "@/components/sessions/session-card";

export default function SessionsPage() {
  const { campaignId } = useParams<{ campaignId: string }>();
  const { data: sessions, isLoading } = useSessions(campaignId);
  const { data: membership } = useMyMembership(campaignId);
  const isDm = membership?.role === "dm";

  const [title, setTitle] = useState("");
  const createSession = useCreateSession(campaignId);

  function handleCreate(event: React.FormEvent) {
    event.preventDefault();
    if (!title.trim()) return;
    createSession.mutate(
      { title: title.trim() },
      { onSuccess: () => setTitle("") },
    );
  }

  return (
    <main className="mx-auto max-w-3xl space-y-6 px-6 py-10">
      <h1 className="text-2xl font-bold">Sessões</h1>

      {isDm ? (
        <form onSubmit={handleCreate} className="flex gap-2">
          <input
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            placeholder="Título da nova sessão"
            className="flex-1 rounded-md border border-border bg-background px-3 py-2 text-sm"
          />
          <button
            type="submit"
            disabled={!title.trim() || createSession.isPending}
            className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:opacity-90 disabled:opacity-50"
          >
            Criar sessão
          </button>
        </form>
      ) : null}
      {createSession.isError ? (
        <p role="alert" className="text-sm text-destructive">
          Não foi possível criar a sessão.
        </p>
      ) : null}

      {isLoading ? (
        <p className="text-sm text-muted-foreground">Carregando…</p>
      ) : sessions && sessions.length > 0 ? (
        <ul className="space-y-2">
          {sessions.map((session) => (
            <li key={session.id}>
              <SessionCard campaignId={campaignId} session={session} />
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-sm text-muted-foreground">
          Nenhuma sessão nesta campanha ainda.
        </p>
      )}
    </main>
  );
}
