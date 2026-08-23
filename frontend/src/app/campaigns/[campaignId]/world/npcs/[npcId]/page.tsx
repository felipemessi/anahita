"use client";

import { useParams } from "next/navigation";

import { MonsterStatBlock } from "@/components/catalog/monster-stat-block";
import { useCatalogEntry } from "@/hooks/use-catalog";
import { useSessions } from "@/hooks/use-session";
import {
  useFactions,
  useLocations,
  useNpcFactions,
  useNpcLocations,
  useNpcs,
  useNpcSessions,
} from "@/hooks/use-world";
import type { NpcLocationPresenceType } from "@/types/world";

const PRESENCE_LABEL: Record<NpcLocationPresenceType, string> = {
  resides: "reside",
  frequents: "frequenta",
  controls: "controla",
};

export default function NpcDetailPage() {
  const { campaignId, npcId } = useParams<{ campaignId: string; npcId: string }>();
  const { data: npcs, isLoading } = useNpcs(campaignId);
  const npc = npcs?.find((candidate) => candidate.id === npcId);

  const { data: factionLinks } = useNpcFactions(npcId);
  const { data: locationLinks } = useNpcLocations(npcId);
  const { data: sessionLinks } = useNpcSessions(npcId);
  const { data: factions } = useFactions(campaignId);
  const { data: locations } = useLocations(campaignId);
  const { data: campaignSessions } = useSessions(campaignId);
  const { data: monster } = useCatalogEntry("monsters", npc?.stat_block_id ?? "");

  const factionsById = new Map((factions ?? []).map((faction) => [faction.id, faction]));
  const locationsById = new Map(
    (locations ?? []).map((location) => [location.id, location]),
  );
  const sessionsById = new Map(
    (campaignSessions ?? []).map((session) => [session.id, session]),
  );

  if (isLoading) {
    return (
      <main className="mx-auto max-w-3xl px-6 py-10">
        <p className="text-sm text-muted-foreground">Carregando…</p>
      </main>
    );
  }
  if (!npc) {
    return (
      <main className="mx-auto max-w-3xl px-6 py-10">
        <p className="text-sm text-muted-foreground">NPC não encontrado.</p>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-3xl space-y-6 px-6 py-10">
      <header>
        <h1 className="text-2xl font-bold">
          {npc.name}
          {!npc.is_alive ? (
            <span className="ml-2 text-sm text-destructive">(falecido)</span>
          ) : null}
        </h1>
        <p className="text-sm text-muted-foreground">
          {npc.race}
          {npc.occupation ? ` · ${npc.occupation}` : ""}
        </p>
      </header>

      {npc.description ? <p className="text-sm">{npc.description}</p> : null}
      {npc.personality ? (
        <p className="text-sm text-muted-foreground">{npc.personality}</p>
      ) : null}

      <section className="space-y-1">
        <h2 className="text-sm font-medium text-muted-foreground">Facções</h2>
        {factionLinks && factionLinks.length > 0 ? (
          <ul className="text-sm">
            {factionLinks.map((link) => (
              <li key={link.id}>
                {factionsById.get(link.faction_id)?.name ?? link.faction_id}
                {link.role_in_faction ? ` — ${link.role_in_faction}` : ""}
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-muted-foreground">Nenhuma.</p>
        )}
      </section>

      <section className="space-y-1">
        <h2 className="text-sm font-medium text-muted-foreground">Locais</h2>
        {locationLinks && locationLinks.length > 0 ? (
          <ul className="text-sm">
            {locationLinks.map((link) => (
              <li key={link.id}>
                {locationsById.get(link.location_id)?.name ?? link.location_id} (
                {PRESENCE_LABEL[link.presence_type]})
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-muted-foreground">Nenhum.</p>
        )}
      </section>

      <section className="space-y-1">
        <h2 className="text-sm font-medium text-muted-foreground">Sessões</h2>
        {sessionLinks && sessionLinks.length > 0 ? (
          <ul className="text-sm">
            {sessionLinks.map((link) => {
              const session = sessionsById.get(link.session_id);
              return (
                <li key={link.id}>
                  {session ? `Sessão ${session.session_number} — ${session.title}` : "Sessão"}
                  {link.appearance_note ? `: ${link.appearance_note}` : ""}
                </li>
              );
            })}
          </ul>
        ) : (
          <p className="text-sm text-muted-foreground">Nenhuma.</p>
        )}
      </section>

      {monster ? <MonsterStatBlock monster={monster} /> : null}
    </main>
  );
}
