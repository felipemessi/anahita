"use client";

import { useState } from "react";

import { MonsterStatBlock } from "@/components/catalog/monster-stat-block";
import { EntityLinkBadge } from "@/components/world/entity-link-badge";
import { useCatalogEntry } from "@/hooks/use-catalog";
import {
  useNpcFactions,
  useNpcLocations,
  useNpcSessions,
} from "@/hooks/use-world";
import type { Npc } from "@/types/world";

/** Summary card for an NPC: name, race, occupation, link badges, and stat block toggle. */
export function NpcCard({ npc }: { npc: Npc }) {
  const [showStatBlock, setShowStatBlock] = useState(false);
  const { data: factions } = useNpcFactions(npc.id);
  const { data: locations } = useNpcLocations(npc.id);
  const { data: sessions } = useNpcSessions(npc.id);
  const { data: monster } = useCatalogEntry("monsters", npc.stat_block_id ?? "");

  return (
    <article className="space-y-2 rounded-lg border border-border bg-card p-4">
      <header className="flex items-center justify-between gap-2">
        <div>
          <p className="font-medium">
            {npc.name}
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

      <div className="flex flex-wrap gap-2">
        <EntityLinkBadge label="facções" count={factions?.length ?? 0} />
        <EntityLinkBadge label="locais" count={locations?.length ?? 0} />
        <EntityLinkBadge label="sessões" count={sessions?.length ?? 0} />
      </div>

      {showStatBlock && monster ? <MonsterStatBlock monster={monster} /> : null}
    </article>
  );
}
