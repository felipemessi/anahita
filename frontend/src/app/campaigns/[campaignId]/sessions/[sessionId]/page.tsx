"use client";

import { useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";

import { useMyMembership } from "@/hooks/use-campaign";
import {
  useCreateEncounter,
  useEncounters,
  useStartEncounter,
} from "@/hooks/use-combat";
import { useMaps } from "@/hooks/use-map";
import {
  useCompleteSession,
  useOpenSession,
  useSessions,
  useUpdateSession,
} from "@/hooks/use-session";
import { MapSection } from "@/components/maps/map-section";
import { MapUpload } from "@/components/maps/map-upload";
import { NoteEditor } from "@/components/sessions/note-editor";

const ENCOUNTER_STATUS_LABEL: Record<string, string> = {
  preparing: "Preparando",
  active: "Em andamento",
  completed: "Concluído",
};

const SESSION_STATUS_LABEL: Record<string, string> = {
  planned: "Planejada",
  in_progress: "Em andamento",
  completed: "Concluída",
};

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

  const { data: encounters } = useEncounters(sessionId);
  const { data: maps } = useMaps(sessionId);
  const [encounterName, setEncounterName] = useState("");
  const createEncounter = useCreateEncounter(sessionId);
  const startEncounter = useStartEncounter();
  const openSession = useOpenSession(campaignId);
  const completeSession = useCompleteSession(campaignId);
  const updateSession = useUpdateSession(campaignId);

  const [isEditingTitle, setIsEditingTitle] = useState(false);
  const [titleDraft, setTitleDraft] = useState("");

  function handleCreateEncounter(event: React.FormEvent) {
    event.preventDefault();
    if (!encounterName.trim()) return;
    createEncounter.mutate(
      { name: encounterName.trim() },
      { onSuccess: () => setEncounterName("") },
    );
  }

  function handleStartEditingTitle(currentTitle: string) {
    setTitleDraft(currentTitle);
    setIsEditingTitle(true);
  }

  function handleSaveTitle(event: React.FormEvent) {
    event.preventDefault();
    const trimmed = titleDraft.trim();
    if (!trimmed) return;
    updateSession.mutate(
      { sessionId, data: { title: trimmed } },
      { onSuccess: () => setIsEditingTitle(false) },
    );
  }

  if (isLoading) {
    return <p className="p-6 text-sm text-muted-foreground">Carregando…</p>;
  }

  if (!session) {
    return <p className="p-6 text-sm text-muted-foreground">Sessão não encontrada.</p>;
  }

  return (
    <main className="mx-auto max-w-3xl space-y-8 px-6 py-10">
      <div>
        <div className="flex items-center justify-between gap-4">
          {isDm && isEditingTitle ? (
            <form onSubmit={handleSaveTitle} className="flex flex-1 items-center gap-2">
              <input
                value={titleDraft}
                onChange={(event) => setTitleDraft(event.target.value)}
                autoFocus
                className="flex-1 rounded-md border border-border bg-background px-3 py-1.5 text-sm"
              />
              <button
                type="submit"
                disabled={!titleDraft.trim() || updateSession.isPending}
                className="shrink-0 rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground hover:opacity-90 disabled:opacity-50"
              >
                Salvar
              </button>
              <button
                type="button"
                onClick={() => setIsEditingTitle(false)}
                className="shrink-0 rounded-md border border-border px-3 py-1.5 text-sm hover:bg-secondary"
              >
                Cancelar
              </button>
            </form>
          ) : (
            <h1 className="text-2xl font-bold">
              Sessão {session.session_number} — {session.title}
              {isDm ? (
                <button
                  type="button"
                  onClick={() => handleStartEditingTitle(session.title)}
                  className="ml-2 text-sm font-normal text-muted-foreground hover:underline"
                >
                  Editar
                </button>
              ) : null}
            </h1>
          )}
          <div className="flex shrink-0 items-center gap-2">
            {isDm && session.status === "planned" ? (
              <button
                type="button"
                onClick={() => openSession.mutate(session.id)}
                disabled={openSession.isPending}
                className="shrink-0 rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground hover:opacity-90 disabled:opacity-50"
              >
                Abrir sessão
              </button>
            ) : (
              <span className="shrink-0 text-xs text-muted-foreground">
                {SESSION_STATUS_LABEL[session.status] ?? session.status}
              </span>
            )}
            {isDm && session.status === "in_progress" ? (
              <button
                type="button"
                onClick={() => completeSession.mutate(session.id)}
                disabled={completeSession.isPending}
                className="shrink-0 rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground hover:opacity-90 disabled:opacity-50"
              >
                Concluir sessão
              </button>
            ) : null}
          </div>
        </div>
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

      <section className="space-y-4">
        <h2 className="font-semibold">Encontros</h2>

        {isDm ? (
          <form onSubmit={handleCreateEncounter} className="flex gap-2">
            <input
              value={encounterName}
              onChange={(event) => setEncounterName(event.target.value)}
              placeholder="Nome do encontro"
              className="flex-1 rounded-md border border-border bg-background px-3 py-2 text-sm"
            />
            <button
              type="submit"
              disabled={!encounterName.trim() || createEncounter.isPending}
              className="rounded-md bg-primary px-3 py-2 text-sm font-medium text-primary-foreground hover:opacity-90 disabled:opacity-50"
            >
              Criar
            </button>
          </form>
        ) : null}

        {encounters && encounters.length > 0 ? (
          <ul className="space-y-2">
            {encounters.map((encounter) => (
              <li
                key={encounter.id}
                className="flex items-center justify-between rounded-lg border border-border bg-card px-4 py-3"
              >
                <div>
                  <p className="font-medium">{encounter.name}</p>
                  <p className="text-xs text-muted-foreground">
                    {ENCOUNTER_STATUS_LABEL[encounter.status] ?? encounter.status}
                  </p>
                </div>
                {isDm && encounter.status === "preparing" ? (
                  <button
                    type="button"
                    onClick={() => startEncounter.mutate(encounter.id)}
                    disabled={startEncounter.isPending}
                    className="rounded-md border border-border px-3 py-1.5 text-sm hover:bg-secondary"
                  >
                    Iniciar
                  </button>
                ) : (
                  <Link
                    href={`/campaigns/${campaignId}/combat/${encounter.id}`}
                    className="rounded-md border border-border px-3 py-1.5 text-sm hover:bg-secondary"
                  >
                    Abrir tracker
                  </Link>
                )}
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-muted-foreground">
            Nenhum encontro nesta sessão ainda.
          </p>
        )}
      </section>

      <section className="space-y-4">
        <h2 className="font-semibold">Mapas</h2>
        {isDm ? <MapUpload sessionId={session.id} /> : null}
        {maps?.map((m) => (
          <MapSection
            key={m.id}
            mapId={m.id}
            isDm={isDm}
            encounterActive={false}
            currentTurnParticipant={undefined}
            participants={[]}
          />
        ))}
      </section>

      <NoteEditor sessionId={session.id} isDm={isDm} />
    </main>
  );
}
