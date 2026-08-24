"use client";

import { useCatalogEntry } from "@/hooks/use-catalog";
import { useRemoveFromInventory, useUpdateInventoryEntry } from "@/hooks/use-inventory";
import type { PartyInventoryEntry } from "@/types/inventory";

/** One stack in the party's shared inventory, resolving its catalog item name. */
export function ItemCard({
  entry,
  campaignId,
  isDm = false,
}: {
  entry: PartyInventoryEntry;
  campaignId: string;
  isDm?: boolean;
}) {
  const { data: item, isLoading } = useCatalogEntry("equipment", entry.item_id);
  const updateEntry = useUpdateInventoryEntry(campaignId);
  const removeEntry = useRemoveFromInventory(campaignId);

  return (
    <article className="flex items-center justify-between gap-3 rounded-lg border border-border bg-card p-4">
      <div>
        <p className="font-medium">
          {isLoading ? "Carregando…" : (item?.name ?? "Item desconhecido")}
        </p>
        {entry.notes ? (
          <p className="text-sm text-muted-foreground">{entry.notes}</p>
        ) : null}
      </div>
      <div className="flex items-center gap-2">
        {isDm ? (
          <input
            type="number"
            min={0}
            value={entry.quantity}
            aria-label={`Quantidade de ${item?.name ?? "item"}`}
            onChange={(event) => {
              const quantity = Number(event.target.value);
              if (Number.isNaN(quantity)) return;
              updateEntry.mutate({ entryId: entry.id, data: { quantity } });
            }}
            className="w-16 rounded-md border border-border bg-background px-2 py-1 text-sm"
          />
        ) : (
          <span className="text-sm">x{entry.quantity}</span>
        )}
        {isDm ? (
          <button
            type="button"
            onClick={() => removeEntry.mutate(entry.id)}
            className="text-xs text-muted-foreground underline hover:no-underline"
          >
            remover
          </button>
        ) : null}
      </div>
    </article>
  );
}
