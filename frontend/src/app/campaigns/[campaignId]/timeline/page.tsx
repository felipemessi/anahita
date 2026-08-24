"use client";

import { useState } from "react";
import { useParams } from "next/navigation";

import { TimelineEventCard } from "@/components/timeline/timeline-event-card";
import { useMyMembership } from "@/hooks/use-campaign";
import { useSessions } from "@/hooks/use-session";
import { useCreateTimelineEvent, useTimeline } from "@/hooks/use-timeline";

export default function TimelinePage() {
  const { campaignId } = useParams<{ campaignId: string }>();
  const { data: entries, isLoading } = useTimeline(campaignId);
  const { data: membership } = useMyMembership(campaignId);
  const { data: sessions } = useSessions(campaignId);
  const isDm = membership?.role === "dm";

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [inGameDate, setInGameDate] = useState("");
  const [sessionId, setSessionId] = useState("");
  const [sortOrder, setSortOrder] = useState("");
  const createEvent = useCreateTimelineEvent(campaignId);

  function handleCreate(event: React.FormEvent) {
    event.preventDefault();
    const parsedSortOrder = Number(sortOrder);
    if (!title.trim() || Number.isNaN(parsedSortOrder)) return;
    createEvent.mutate(
      {
        title: title.trim(),
        description: description.trim() || null,
        in_game_date: inGameDate.trim() || null,
        session_id: sessionId || null,
        sort_order: parsedSortOrder,
      },
      {
        onSuccess: () => {
          setTitle("");
          setDescription("");
          setInGameDate("");
          setSessionId("");
          setSortOrder("");
        },
      },
    );
  }

  return (
    <main className="mx-auto max-w-3xl space-y-6 px-6 py-10">
      <h1 className="text-2xl font-bold">Timeline</h1>

      {isDm ? (
        <form onSubmit={handleCreate} className="space-y-2 rounded-lg border border-border bg-card p-4">
          <p className="text-sm font-medium">Adicionar marco</p>
          <input
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            placeholder="Título"
            className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
          />
          <textarea
            value={description}
            onChange={(event) => setDescription(event.target.value)}
            placeholder="Descrição (opcional)"
            rows={2}
            className="w-full resize-none rounded-md border border-border bg-background px-3 py-2 text-sm"
          />
          <div className="flex flex-wrap gap-2">
            <input
              value={inGameDate}
              onChange={(event) => setInGameDate(event.target.value)}
              placeholder="Data in-game (opcional)"
              className="flex-1 rounded-md border border-border bg-background px-3 py-2 text-sm"
            />
            <input
              value={sortOrder}
              onChange={(event) => setSortOrder(event.target.value)}
              type="number"
              placeholder="Ordem"
              aria-label="Posição de ordenação"
              className="w-24 rounded-md border border-border bg-background px-3 py-2 text-sm"
            />
          </div>
          <select
            value={sessionId}
            onChange={(event) => setSessionId(event.target.value)}
            aria-label="Sessão âncora (opcional)"
            className="w-full rounded-md border border-border bg-background px-2 py-1.5 text-sm"
          >
            <option value="">Sem sessão âncora</option>
            {sessions?.map((session) => (
              <option key={session.id} value={session.id}>
                Sessão {session.session_number} — {session.title}
              </option>
            ))}
          </select>
          <button
            type="submit"
            disabled={!title.trim() || sortOrder.trim() === "" || createEvent.isPending}
            className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:opacity-90 disabled:opacity-50"
          >
            Adicionar marco
          </button>
          {createEvent.isError ? (
            <p role="alert" className="text-sm text-destructive">
              Não foi possível criar o marco.
            </p>
          ) : null}
        </form>
      ) : null}

      {isLoading ? (
        <p className="text-sm text-muted-foreground">Carregando…</p>
      ) : entries && entries.length > 0 ? (
        <ol className="space-y-2">
          {entries.map((entry) => (
            <li key={`${entry.entry_type}-${entry.id}`}>
              <TimelineEventCard campaignId={campaignId} entry={entry} isDm={isDm} />
            </li>
          ))}
        </ol>
      ) : (
        <p className="text-sm text-muted-foreground">Nada na timeline ainda.</p>
      )}
    </main>
  );
}
