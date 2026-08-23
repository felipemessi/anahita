"use client";

import { useState } from "react";
import { useParams } from "next/navigation";

import { FactionGraph } from "@/components/world/faction-graph";
import { useMyMembership } from "@/hooks/use-campaign";
import { useCreateFaction, useFactions } from "@/hooks/use-world";

export default function FactionsPage() {
  const { campaignId } = useParams<{ campaignId: string }>();
  const { data: factions, isLoading } = useFactions(campaignId);
  const { data: membership } = useMyMembership(campaignId);
  const isDm = membership?.role === "dm";

  const [name, setName] = useState("");
  const createFaction = useCreateFaction(campaignId);

  function handleCreate(event: React.FormEvent) {
    event.preventDefault();
    if (!name.trim()) return;
    createFaction.mutate(
      { name: name.trim(), description: "" },
      { onSuccess: () => setName("") },
    );
  }

  return (
    <main className="mx-auto max-w-3xl space-y-6 px-6 py-10">
      <h1 className="text-2xl font-bold">Facções</h1>

      {isDm ? (
        <form onSubmit={handleCreate} className="flex gap-2">
          <input
            value={name}
            onChange={(event) => setName(event.target.value)}
            placeholder="Nome da facção"
            className="flex-1 rounded-md border border-border bg-background px-3 py-2 text-sm"
          />
          <button
            type="submit"
            disabled={!name.trim() || createFaction.isPending}
            className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:opacity-90 disabled:opacity-50"
          >
            Criar facção
          </button>
        </form>
      ) : null}
      {createFaction.isError ? (
        <p role="alert" className="text-sm text-destructive">
          Não foi possível criar a facção.
        </p>
      ) : null}

      {isLoading ? (
        <p className="text-sm text-muted-foreground">Carregando…</p>
      ) : (
        <FactionGraph factions={factions ?? []} campaignId={campaignId} />
      )}
    </main>
  );
}
