"use client";

import { useState } from "react";
import { useParams } from "next/navigation";

import { NpcCard } from "@/components/world/npc-card";
import { useMyMembership } from "@/hooks/use-campaign";
import { useCatalogEntry, useCatalogList } from "@/hooks/use-catalog";
import { useCreateNpc, useNpcs } from "@/hooks/use-world";

export default function NpcsPage() {
  const { campaignId } = useParams<{ campaignId: string }>();
  const { data: npcs, isLoading } = useNpcs(campaignId);
  const { data: membership } = useMyMembership(campaignId);
  const isDm = membership?.role === "dm";

  const [name, setName] = useState("");
  const [race, setRace] = useState("");
  const [statBlockSearch, setStatBlockSearch] = useState("");
  const [statBlockId, setStatBlockId] = useState<string | null>(null);
  const createNpc = useCreateNpc(campaignId);

  const { data: monsterMatches } = useCatalogList("monsters", {
    search: statBlockSearch,
    campaign_id: campaignId,
  });
  const { data: selectedMonster } = useCatalogEntry("monsters", statBlockId ?? "");

  function handleCreate(event: React.FormEvent) {
    event.preventDefault();
    if (!name.trim() || !race.trim()) return;
    createNpc.mutate(
      {
        name: name.trim(),
        race: race.trim(),
        description: "",
        stat_block_id: statBlockId,
      },
      {
        onSuccess: () => {
          setName("");
          setRace("");
          setStatBlockSearch("");
          setStatBlockId(null);
        },
      },
    );
  }

  return (
    <main className="mx-auto max-w-3xl space-y-6 px-6 py-10">
      <h1 className="text-2xl font-bold">NPCs</h1>

      {isDm ? (
        <form onSubmit={handleCreate} className="flex flex-wrap gap-2">
          <input
            value={name}
            onChange={(event) => setName(event.target.value)}
            placeholder="Nome"
            className="flex-1 rounded-md border border-border bg-background px-3 py-2 text-sm"
          />
          <input
            value={race}
            onChange={(event) => setRace(event.target.value)}
            placeholder="Raça"
            className="w-32 rounded-md border border-border bg-background px-3 py-2 text-sm"
          />
          <div className="w-full">
            {selectedMonster ? (
              <p className="text-xs text-muted-foreground">
                Stat block: {selectedMonster.name}{" "}
                <button
                  type="button"
                  onClick={() => setStatBlockId(null)}
                  className="underline hover:no-underline"
                >
                  remover
                </button>
              </p>
            ) : (
              <input
                value={statBlockSearch}
                onChange={(event) => setStatBlockSearch(event.target.value)}
                placeholder="Buscar stat block no catálogo de monstros (opcional)"
                className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
              />
            )}
            {!selectedMonster && statBlockSearch && monsterMatches && monsterMatches.length > 0 ? (
              <ul className="mt-1 max-h-32 space-y-1 overflow-y-auto rounded-md border border-border">
                {monsterMatches.map((monster) => (
                  <li key={monster.id}>
                    <button
                      type="button"
                      onClick={() => setStatBlockId(monster.id)}
                      className="flex w-full items-center justify-between px-3 py-1.5 text-left text-sm hover:bg-secondary"
                    >
                      <span>{monster.name}</span>
                      <span className="text-xs text-muted-foreground">
                        CR {monster.challenge_rating}
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            ) : null}
          </div>
          <button
            type="submit"
            disabled={!name.trim() || !race.trim() || createNpc.isPending}
            className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:opacity-90 disabled:opacity-50"
          >
            Criar NPC
          </button>
        </form>
      ) : null}
      {createNpc.isError ? (
        <p role="alert" className="text-sm text-destructive">
          Não foi possível criar o NPC.
        </p>
      ) : null}

      {isLoading ? (
        <p className="text-sm text-muted-foreground">Carregando…</p>
      ) : npcs && npcs.length > 0 ? (
        <ul className="space-y-2">
          {npcs.map((npc) => (
            <li key={npc.id}>
              <NpcCard npc={npc} campaignId={campaignId} isDm={isDm} />
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-sm text-muted-foreground">
          Nenhum NPC nesta campanha ainda.
        </p>
      )}
    </main>
  );
}
