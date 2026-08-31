"use client";

import { useCatalogEntry } from "@/hooks/use-catalog";
import { useClaimLootDrop } from "@/hooks/use-inventory";
import type { LootDrop } from "@/types/inventory";
import type { Character, CharacterSummary } from "@/types/character";

/** Copper-piece total, formatted as gp/sp/cp (1gp = 10sp = 100cp). */
function formatCurrency(currencyCp: number): string {
  if (currencyCp <= 0) return "";
  const gp = Math.floor(currencyCp / 100);
  const sp = Math.floor((currencyCp % 100) / 10);
  const cp = currencyCp % 10;
  return [gp ? `${gp}po` : null, sp ? `${sp}pp` : null, cp ? `${cp}pc` : null]
    .filter(Boolean)
    .join(" ");
}

function LootDropRow({
  drop,
  campaignId,
  myCharacterId,
  isDm,
  characters,
}: {
  drop: LootDrop;
  campaignId: string;
  myCharacterId: string | null;
  isDm: boolean;
  characters: (Character | CharacterSummary)[];
}) {
  const { data: catalogItem } = useCatalogEntry("equipment", drop.item_id ?? "");
  const { data: magicItem } = useCatalogEntry("magic-items", drop.magic_item_id ?? "");
  const claim = useClaimLootDrop(campaignId);

  const name =
    catalogItem?.name ?? magicItem?.name ?? drop.custom_item_name ?? "Moeda";
  const currency = formatCurrency(drop.currency_cp);

  return (
    <tr>
      <td className="px-3 py-2">
        {name}
        {drop.quantity > 1 ? ` x${drop.quantity}` : ""}
      </td>
      <td className="px-3 py-2 text-sm text-muted-foreground">{currency}</td>
      <td className="px-3 py-2 text-right">
        {drop.claimed_by ? (
          <span className="text-xs text-muted-foreground">reivindicado</span>
        ) : (
          <div className="flex items-center justify-end gap-2">
            {myCharacterId ? (
              <button
                type="button"
                onClick={() =>
                  claim.mutate({
                    lootDropId: drop.id,
                    data: { character_id: myCharacterId },
                  })
                }
                disabled={claim.isPending}
                className="rounded-md border border-border px-3 py-1 text-xs hover:bg-secondary/50 disabled:opacity-50"
              >
                Reivindicar
              </button>
            ) : null}
            {isDm ? (
              <select
                value=""
                onChange={(event) => {
                  const characterId = event.target.value;
                  if (!characterId) return;
                  claim.mutate({
                    lootDropId: drop.id,
                    data: { character_id: characterId },
                  });
                }}
                disabled={claim.isPending}
                aria-label="Atribuir a..."
                className="rounded-md border border-border bg-background px-2 py-1 text-xs disabled:opacity-50"
              >
                <option value="">Atribuir a...</option>
                {characters.map((character) => (
                  <option key={character.id} value={character.id}>
                    {character.name}
                  </option>
                ))}
              </select>
            ) : null}
          </div>
        )}
      </td>
    </tr>
  );
}

/** Loot drops from the campaign's encounters — catalog, magic, and custom items, plus currency. */
export function LootTable({
  lootDrops,
  campaignId,
  myCharacterId,
  isDm = false,
  characters = [],
}: {
  lootDrops: LootDrop[];
  campaignId: string;
  myCharacterId: string | null;
  /** DM sees an "atribuir a..." menu per unclaimed drop, listing the campaign's characters. */
  isDm?: boolean;
  characters?: (Character | CharacterSummary)[];
}) {
  if (lootDrops.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">Nenhum loot registrado ainda.</p>
    );
  }

  return (
    <table className="w-full text-left">
      <thead>
        <tr className="text-xs text-muted-foreground">
          <th className="px-3 py-1 font-normal">Item</th>
          <th className="px-3 py-1 font-normal">Moeda</th>
          <th className="px-3 py-1"></th>
        </tr>
      </thead>
      <tbody className="divide-y divide-border">
        {lootDrops.map((drop) => (
          <LootDropRow
            key={drop.id}
            drop={drop}
            campaignId={campaignId}
            myCharacterId={myCharacterId}
            isDm={isDm}
            characters={characters}
          />
        ))}
      </tbody>
    </table>
  );
}
