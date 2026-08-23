"use client";

import { useState } from "react";
import Link from "next/link";

import { MonsterStatBlock } from "@/components/catalog/monster-stat-block";
import { EntityLinkBadge } from "@/components/world/entity-link-badge";
import { useCatalogEntry } from "@/hooks/use-catalog";
import { useSessions } from "@/hooks/use-session";
import {
  useLinkNpcSession,
  useNpcFactions,
  useNpcLocations,
  useNpcSessions,
} from "@/hooks/use-world";
import type { Npc } from "@/types/world";

/** Summary card for an NPC: name, race, occupation, link badges, and stat block toggle. */
export function NpcCard({
  npc,
  campaignId,
  isDm = false,
}: {
  npc: Npc;
  campaignId: string;
  isDm?: boolean;
}) {
  const [showStatBlock, setShowStatBlock] = useState(false);
  const [showLinkSession, setShowLinkSession] = useState(false);
  const [sessionId, setSessionId] = useState("");
  const { data: factions } = useNpcFactions(npc.id);
  const { data: locations } = useNpcLocations(npc.id);
  const { data: sessions } = useNpcSessions(npc.id);
  const { data: campaignSessions } = useSessions(campaignId);
  const { data: monster } = useCatalogEntry("monsters", npc.stat_block_id ?? "");
  const linkSession = useLinkNpcSession(npc.id);

  function handleLinkSession(event: React.FormEvent) {
    event.preventDefault();
    if (!sessionId) return;
    linkSession.mutate(
      { session_id: sessionId },
      { onSuccess: () => setSessionId("") },
    );
  }

  return (
    <article className="space-y-2 rounded-lg border border-border bg-card p-4">
      <header className="flex items-center justify-between gap-2">
        <div>
          <p className="font-medium">
            <Link
              href={`/campaigns/${campaignId}/world/npcs/${npc.id}`}
              className="hover:underline"
            >
              {npc.name}
            </Link>
            {!npc.is_alive ? (
              <span className="ml-2 text-xs text-destructive">(falecido)</span>
            ) : null}
          </p>
          <p className="text-sm text-muted-foreground">
            {npc.race}
            {npc.occupation ? ` · ${npc.occupation}` : ""}
          </p>
        </div>
        {npc.stat_block_id ? (
          <button
            type="button"
            onClick={() => setShowStatBlock((visible) => !visible)}
            className="shrink-0 rounded-md border border-border px-3 py-1 text-xs hover:bg-secondary/50"
          >
            {showStatBlock ? "Ocultar stat block" : "Ver stat block"}
          </button>
        ) : null}
      </header>

      {npc.description ? <p className="text-sm">{npc.description}</p> : null}

      <div className="flex flex-wrap items-center gap-2">
        <EntityLinkBadge label="facções" count={factions?.length ?? 0} />
        <EntityLinkBadge label="locais" count={locations?.length ?? 0} />
        <EntityLinkBadge label="sessões" count={sessions?.length ?? 0} />
        {isDm ? (
          <button
            type="button"
            onClick={() => setShowLinkSession((visible) => !visible)}
            className="text-xs text-muted-foreground underline hover:no-underline"
          >
            Vincular a uma sessão
          </button>
        ) : null}
      </div>

      {showLinkSession ? (
        <form onSubmit={handleLinkSession} className="flex gap-2">
          <select
            value={sessionId}
            onChange={(event) => setSessionId(event.target.value)}
            aria-label={`Sessão em que ${npc.name} apareceu`}
            className="flex-1 rounded-md border border-border bg-background px-2 py-1.5 text-xs"
          >
            <option value="">Selecione uma sessão</option>
            {campaignSessions?.map((session) => (
              <option key={session.id} value={session.id}>
                Sessão {session.session_number} — {session.title}
              </option>
            ))}
          </select>
          <button
            type="submit"
            disabled={!sessionId || linkSession.isPending}
            className="rounded-md border border-border px-3 py-1 text-xs hover:bg-secondary/50 disabled:opacity-50"
          >
            Vincular
          </button>
        </form>
      ) : null}

      {showStatBlock && monster ? <MonsterStatBlock monster={monster} /> : null}
    </article>
  );
}
