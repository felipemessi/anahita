"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";

import { useCharacterSessions } from "@/hooks/use-character";
import type { SessionStatus } from "@/types/session";

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
 * Kept deliberately isolated: the next backlog story ("reordenar sessões
 * na ficha") adds drag-and-drop reordering inside this same dropdown.
 */
export function CharacterSessionsDropdown({
  campaignId,
  characterId,
}: {
  campaignId: string;
  characterId: string;
}) {
  const { data: sessions, isLoading } = useCharacterSessions(characterId);
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

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
          {isLoading ? (
            <p className="px-3 py-2 text-sm text-muted-foreground">Carregando…</p>
          ) : !sessions || sessions.length === 0 ? (
            <p className="px-3 py-2 text-sm text-muted-foreground">
              Este personagem ainda não participou de nenhuma sessão.
            </p>
          ) : (
            sessions.map((session) => (
              <Link
                key={session.id}
                href={`/campaigns/${campaignId}/sessions/${session.id}`}
                role="menuitem"
                onClick={() => setOpen(false)}
                className="flex items-center justify-between gap-2 rounded-md px-3 py-2 text-sm hover:bg-secondary/50"
              >
                <span className="truncate">
                  Sessão {session.session_number} — {session.title}
                </span>
                <span className="shrink-0 text-xs text-muted-foreground">
                  {STATUS_LABEL[session.status]}
                </span>
              </Link>
            ))
          )}
        </div>
      ) : null}
    </div>
  );
}
