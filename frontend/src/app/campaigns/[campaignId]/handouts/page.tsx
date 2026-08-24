"use client";

import { useRef, useState } from "react";
import { useParams } from "next/navigation";

import { HandoutCard } from "@/components/handouts/handout-card";
import { useMyMembership } from "@/hooks/use-campaign";
import { useCreateHandout, useHandoutRevealListener, useHandouts } from "@/hooks/use-handouts";
import { useSessions } from "@/hooks/use-session";
import type { HandoutType } from "@/types/handout";

export default function HandoutsPage() {
  const { campaignId } = useParams<{ campaignId: string }>();
  const { data: membership } = useMyMembership(campaignId);
  const isDm = membership?.role === "dm";
  const { data: sessions } = useSessions(campaignId);
  const { data: handouts, isLoading } = useHandouts(campaignId);

  const [sessionFilter, setSessionFilter] = useState("");
  useHandoutRevealListener(campaignId, sessionFilter || null);

  const [title, setTitle] = useState("");
  const [handoutType, setHandoutType] = useState<HandoutType>("text");
  const [content, setContent] = useState("");
  const [createSessionId, setCreateSessionId] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);
  const createHandout = useCreateHandout(campaignId);

  function handleCreate(event: React.FormEvent) {
    event.preventDefault();
    if (!title.trim()) return;
    createHandout.mutate(
      {
        fields: {
          title: title.trim(),
          handout_type: handoutType,
          content: content.trim() || undefined,
          session_id: createSessionId || undefined,
        },
        file: fileInputRef.current?.files?.[0] ?? null,
      },
      {
        onSuccess: () => {
          setTitle("");
          setContent("");
          setCreateSessionId("");
          if (fileInputRef.current) fileInputRef.current.value = "";
        },
      },
    );
  }

  const filteredHandouts = sessionFilter
    ? handouts?.filter((h) => h.session_id === sessionFilter)
    : handouts;

  return (
    <main className="mx-auto max-w-3xl space-y-6 px-6 py-10">
      <h1 className="text-2xl font-bold">Handouts</h1>

      <select
        value={sessionFilter}
        onChange={(event) => setSessionFilter(event.target.value)}
        aria-label="Filtrar por sessão"
        className="rounded-md border border-border bg-background px-2 py-2 text-sm"
      >
        <option value="">Todas as sessões</option>
        {sessions?.map((session) => (
          <option key={session.id} value={session.id}>
            Sessão {session.session_number} — {session.title}
          </option>
        ))}
      </select>

      {isDm ? (
        <form onSubmit={handleCreate} className="space-y-2 rounded-lg border border-border p-4">
          <div className="flex flex-wrap gap-2">
            <input
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              placeholder="Título"
              className="flex-1 rounded-md border border-border bg-background px-3 py-2 text-sm"
            />
            <select
              value={handoutType}
              onChange={(event) => setHandoutType(event.target.value as HandoutType)}
              aria-label="Tipo de handout"
              className="rounded-md border border-border bg-background px-2 py-2 text-sm"
            >
              <option value="text">Texto</option>
              <option value="image">Imagem</option>
              <option value="map">Mapa</option>
            </select>
            <select
              value={createSessionId}
              onChange={(event) => setCreateSessionId(event.target.value)}
              aria-label="Sessão (opcional)"
              className="rounded-md border border-border bg-background px-2 py-2 text-sm"
            >
              <option value="">Sem sessão específica</option>
              {sessions?.map((session) => (
                <option key={session.id} value={session.id}>
                  Sessão {session.session_number} — {session.title}
                </option>
              ))}
            </select>
          </div>

          {handoutType === "text" ? (
            <textarea
              value={content}
              onChange={(event) => setContent(event.target.value)}
              placeholder="Conteúdo"
              className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
            />
          ) : (
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              aria-label="Arquivo de imagem ou mapa"
              className="w-full text-sm"
            />
          )}

          <button
            type="submit"
            disabled={!title.trim() || createHandout.isPending}
            className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:opacity-90 disabled:opacity-50"
          >
            Criar handout
          </button>
        </form>
      ) : null}

      {isLoading ? (
        <p className="text-sm text-muted-foreground">Carregando…</p>
      ) : filteredHandouts && filteredHandouts.length > 0 ? (
        <ul className="space-y-2">
          {filteredHandouts.map((handout) => (
            <li key={handout.id}>
              <HandoutCard handout={handout} campaignId={campaignId} isDm={isDm} />
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-sm text-muted-foreground">Nenhum handout ainda.</p>
      )}
    </main>
  );
}
