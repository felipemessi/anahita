"use client";

import { useState } from "react";
import { useParams } from "next/navigation";

import { ItemCard } from "@/components/inventory/item-card";
import { LootTable } from "@/components/inventory/loot-table";
import { useCharacters } from "@/hooks/use-character";
import { useMyMembership } from "@/hooks/use-campaign";
import { useCatalogList } from "@/hooks/use-catalog";
import {
  useAddToInventory,
  useCampaignEncounters,
  useCampaignLootDrops,
  useCreateLootDrop,
  usePartyInventory,
} from "@/hooks/use-inventory";

export default function InventoryPage() {
  const { campaignId } = useParams<{ campaignId: string }>();
  const { data: membership } = useMyMembership(campaignId);
  const isDm = membership?.role === "dm";
  const { data: characters } = useCharacters(campaignId);
  const myCharacterId =
    characters?.find((c) => c.campaign_member_id === membership?.id)?.id ?? null;

  const { data: inventory, isLoading: loadingInventory } = usePartyInventory(campaignId);
  const { data: lootDrops, isLoading: loadingLoot } = useCampaignLootDrops(campaignId);
  const { data: encounters } = useCampaignEncounters(campaignId);

  const [itemSearch, setItemSearch] = useState("");
  const [itemId, setItemId] = useState<string | null>(null);
  const { data: itemMatches } = useCatalogList("equipment", {
    search: itemSearch,
    campaign_id: campaignId,
  });
  const addToInventory = useAddToInventory(campaignId);

  const [lootEncounterId, setLootEncounterId] = useState("");
  const [lootItemName, setLootItemName] = useState("");
  const [lootCurrency, setLootCurrency] = useState("");
  const createLootDrop = useCreateLootDrop(campaignId);

  function handleAddItem(event: React.FormEvent) {
    event.preventDefault();
    if (!itemId) return;
    addToInventory.mutate(
      { item_id: itemId, quantity: 1 },
      { onSuccess: () => setItemId(null) },
    );
    setItemSearch("");
  }

  function handleCreateLoot(event: React.FormEvent) {
    event.preventDefault();
    const currencyCp = Number(lootCurrency) || 0;
    if (!lootEncounterId || (!lootItemName.trim() && currencyCp <= 0)) return;
    createLootDrop.mutate(
      {
        encounterId: lootEncounterId,
        data: {
          custom_item_name: lootItemName.trim() || undefined,
          currency_cp: currencyCp,
        },
      },
      {
        onSuccess: () => {
          setLootItemName("");
          setLootCurrency("");
        },
      },
    );
  }

  return (
    <main className="mx-auto max-w-3xl space-y-8 px-6 py-10">
      <h1 className="text-2xl font-bold">Inventário</h1>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold">Inventário do grupo</h2>

        {isDm ? (
          <form onSubmit={handleAddItem} className="flex flex-wrap gap-2">
            <input
              value={itemSearch}
              onChange={(event) => {
                setItemSearch(event.target.value);
                setItemId(null);
              }}
              placeholder="Buscar item no catálogo"
              className="flex-1 rounded-md border border-border bg-background px-3 py-2 text-sm"
            />
            <button
              type="submit"
              disabled={!itemId || addToInventory.isPending}
              className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:opacity-90 disabled:opacity-50"
            >
              Adicionar
            </button>
            {itemSearch && !itemId && itemMatches && itemMatches.length > 0 ? (
              <ul className="w-full max-h-32 space-y-1 overflow-y-auto rounded-md border border-border">
                {itemMatches.map((item) => (
                  <li key={item.id}>
                    <button
                      type="button"
                      onClick={() => setItemId(item.id)}
                      className="w-full px-3 py-1.5 text-left text-sm hover:bg-secondary"
                    >
                      {item.name}
                    </button>
                  </li>
                ))}
              </ul>
            ) : null}
          </form>
        ) : null}

        {loadingInventory ? (
          <p className="text-sm text-muted-foreground">Carregando…</p>
        ) : inventory && inventory.length > 0 ? (
          <ul className="space-y-2">
            {inventory.map((entry) => (
              <li key={entry.id}>
                <ItemCard entry={entry} campaignId={campaignId} isDm={isDm} />
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-muted-foreground">Inventário vazio.</p>
        )}
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold">Loot</h2>

        {isDm ? (
          <form onSubmit={handleCreateLoot} className="flex flex-wrap gap-2">
            <select
              value={lootEncounterId}
              onChange={(event) => setLootEncounterId(event.target.value)}
              aria-label="Encontro"
              className="rounded-md border border-border bg-background px-2 py-2 text-sm"
            >
              <option value="">Selecione um encontro</option>
              {encounters?.map((encounter) => (
                <option key={encounter.id} value={encounter.id}>
                  {encounter.name}
                </option>
              ))}
            </select>
            <input
              value={lootItemName}
              onChange={(event) => setLootItemName(event.target.value)}
              placeholder="Nome do item (livre)"
              className="flex-1 rounded-md border border-border bg-background px-3 py-2 text-sm"
            />
            <input
              value={lootCurrency}
              onChange={(event) => setLootCurrency(event.target.value)}
              placeholder="Moeda (cp)"
              inputMode="numeric"
              className="w-28 rounded-md border border-border bg-background px-3 py-2 text-sm"
            />
            <button
              type="submit"
              disabled={!lootEncounterId || createLootDrop.isPending}
              className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:opacity-90 disabled:opacity-50"
            >
              Distribuir loot
            </button>
          </form>
        ) : null}

        {loadingLoot ? (
          <p className="text-sm text-muted-foreground">Carregando…</p>
        ) : (
          <LootTable
            lootDrops={lootDrops ?? []}
            campaignId={campaignId}
            myCharacterId={myCharacterId}
            isDm={isDm}
            characters={characters ?? []}
          />
        )}
      </section>
    </main>
  );
}
