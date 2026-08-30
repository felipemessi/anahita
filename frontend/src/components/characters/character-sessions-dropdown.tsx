"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";

import { useCharacterSessions, useReorderCharacterSessions } from "@/hooks/use-character";
import { ApiError } from "@/lib/api/client";
import type { GameSession, SessionStatus } from "@/types/session";

const STATUS_LABEL: Record<SessionStatus, string> = {
  planned: "Planejada",
  in_progress: "Em andamento",
  completed: "Concluída",
};

/**
 * Dropdown listing the sessions a character has actually appeared in
 * (combat participation), for the ficha's header (Fase 10). The list
 * scrolls internally past a fixed height instead of growing the page —
 * that's the "overflow" the story asks for.
 *
 * Reorder buttons (up/down, not drag-and-drop — simpler and more
 * accessible) let the owner set a personal display order, saved via
 * `PATCH /characters/{id}/sessions/order`. Owner-only server-side, same
 * pattern as `CharacterPortrait`/`CharacterInfoEditor`: the buttons render
 * for any viewer and a non-owner's request is rejected by the backend
 * rather than hidden here, since the ficha page doesn't otherwise carry an
 * "is this viewer the owner" flag.
 */
export function CharacterSessionsDropdown({
  campaignId,
  characterId,
}: {
  campaignId: string;
  characterId: string;
}) {
  const { data: sessions, isLoading } = useCharacterSessions(characterId);
  const reorderSessions = useReorderCharacterSessions(characterId);
  const [open, setOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  function handleMove(session: GameSession, direction: -1 | 1) {
    if (!sessions) return;
    const index = sessions.findIndex((s) => s.id === session.id);
    const targetIndex = index + direction;
    if (index === -1 || targetIndex < 0 || targetIndex >= sessions.length) return;

    const reordered = [...sessions];
    reordered.splice(targetIndex, 0, ...reordered.splice(index, 1));

    setError(null);
    reorderSessions.mutate(
      reordered.map((s) => s.id),
      {
        onError: (err) => {
          setError(
            err instanceof ApiError ? err.message : "Não foi possível reordenar as sessões.",
          );
        },
      },
    );
  }

  useEffect(() => {
    if (!open) return;

    function handlePointerDown(event: MouseEvent) {
      if (!containerRef.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    }
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") setOpen(false);
    }

    document.addEventListener("mousedown", handlePointerDown);
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("mousedown", handlePointerDown);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [open]);

  return (
    <div ref={containerRef} className="relative">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        aria-haspopup="true"
        className="flex items-center gap-1.5 rounded-md border border-border px-3 py-1.5 text-sm hover:bg-secondary"
      >
        Sessões
        {sessions && sessions.length > 0 ? (
          <span className="rounded-full bg-secondary px-1.5 text-xs text-secondary-foreground">
            {sessions.length}
          </span>
        ) : null}
        <span aria-hidden="true">▾</span>
      </button>

      {open ? (
        <div
          role="menu"
          aria-label="Sessões do personagem"
          className="absolute right-0 z-20 mt-1 max-h-72 w-64 overflow-y-auto rounded-lg border border-border bg-card p-1 shadow-lg"
        >
          {error ? (
            <p role="alert" className="px-3 py-2 text-sm text-destructive">
              {error}
            </p>
          ) : null}
          {isLoading ? (
            <p className="px-3 py-2 text-sm text-muted-foreground">Carregando…</p>
          ) : !sessions || sessions.length === 0 ? (
            <p className="px-3 py-2 text-sm text-muted-foreground">
              Este personagem ainda não participou de nenhuma sessão.
            </p>
          ) : (
            sessions.map((session, index) => (
              <div key={session.id} className="flex items-center gap-1">
                <Link
                  href={`/campaigns/${campaignId}/sessions/${session.id}`}
                  role="menuitem"
                  onClick={() => setOpen(false)}
                  className="flex flex-1 items-center justify-between gap-2 rounded-md px-3 py-2 text-sm hover:bg-secondary/50"
                >
                  <span className="truncate">
                    Sessão {session.session_number} — {session.title}
                  </span>
                  <span className="shrink-0 text-xs text-muted-foreground">
                    {STATUS_LABEL[session.status]}
                  </span>
                </Link>
                <div className="flex shrink-0 flex-col">
                  <button
                    type="button"
                    aria-label={`Mover sessão ${session.title} para cima`}
                    disabled={index === 0 || reorderSessions.isPending}
                    onClick={() => handleMove(session, -1)}
                    className="leading-none text-muted-foreground hover:text-foreground disabled:opacity-30"
                  >
                    ▲
                  </button>
                  <button
                    type="button"
                    aria-label={`Mover sessão ${session.title} para baixo`}
                    disabled={index === sessions.length - 1 || reorderSessions.isPending}
                    onClick={() => handleMove(session, 1)}
                    className="leading-none text-muted-foreground hover:text-foreground disabled:opacity-30"
                  >
                    ▼
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      ) : null}
    </div>
  );
}
