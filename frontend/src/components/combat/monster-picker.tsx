"use client";

import { useEffect, useState } from "react";

import { useCatalogEntry, useCatalogList } from "@/hooks/use-catalog";
import { useCombat } from "@/hooks/use-combat";

/**
 * Add-participant form: search the campaign's Monster catalog (SRD +
 * homebrew) to autocomplete name/HP/AC, or type every field by hand for an
 * NPC without a stat block. Initiative and turn order are always manual —
 * the DM sets marching order at the table, the catalog has no opinion on it.
 */
export function MonsterPicker({ campaignId }: { campaignId: string }) {
  const { addParticipant } = useCombat();

  const [search, setSearch] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [hitPointMax, setHitPointMax] = useState("");
  const [armorClass, setArmorClass] = useState("");
  const [initiative, setInitiative] = useState("");
  const [turnOrder, setTurnOrder] = useState("");

  const { data: monsters } = useCatalogList("monsters", {
    search,
    campaign_id: campaignId,
  });
  const { data: monster } = useCatalogEntry("monsters", selectedId ?? "");

  // Autofill name/HP/AC once the picked monster's full detail resolves.
  useEffect(() => {
    if (!monster) return;
    setName(monster.name);
    setHitPointMax(String(monster.hit_points));
    setArmorClass(String(monster.armor_classes[0]?.value ?? 10));
  }, [monster]);

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    const hp = Number(hitPointMax);
    const ac = Number(armorClass);
    const init = Number(initiative);
    const order = Number(turnOrder);
    if (!name.trim() || !Number.isFinite(hp) || hp < 1) return;
    if (!Number.isFinite(ac) || ac < 0) return;
    if (!Number.isFinite(init) || !Number.isFinite(order)) return;

    addParticipant({
      npc_id: null,
      character_id: null,
      name: name.trim(),
      hit_point_max: hp,
      armor_class: ac,
      initiative: init,
      turn_order: order,
    });

    setSearch("");
    setSelectedId(null);
    setName("");
    setHitPointMax("");
    setArmorClass("");
    setInitiative("");
    setTurnOrder("");
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-2 rounded-lg border border-border p-3">
      <div>
        <label htmlFor="monster-picker-search" className="text-xs text-muted-foreground">
          Buscar monstro no catálogo
        </label>
        <input
          id="monster-picker-search"
          type="search"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          placeholder="Nome do monstro…"
          className="mt-1 w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
        />
        {search && monsters && monsters.length > 0 ? (
          <ul className="mt-1 max-h-32 space-y-1 overflow-y-auto rounded-md border border-border">
            {monsters.map((m) => (
              <li key={m.id}>
                <button
                  type="button"
                  onClick={() => setSelectedId(m.id)}
                  className="flex w-full items-center justify-between px-3 py-1.5 text-left text-sm hover:bg-secondary"
                >
                  <span>{m.name}</span>
                  <span className="text-xs text-muted-foreground">CR {m.challenge_rating}</span>
                </button>
              </li>
            ))}
          </ul>
        ) : null}
      </div>

      <p className="text-xs text-muted-foreground">
        Ou preencha os campos manualmente (NPC sem stat block):
      </p>

      <div className="grid grid-cols-2 gap-2">
        <label className="col-span-2 text-xs">
          Nome
          <input
            value={name}
            onChange={(event) => setName(event.target.value)}
            className="mt-1 w-full rounded-md border border-border bg-background px-2 py-1.5 text-sm"
          />
        </label>
        <label className="text-xs">
          PV máximo
          <input
            type="number"
            min={1}
            value={hitPointMax}
            onChange={(event) => setHitPointMax(event.target.value)}
            className="mt-1 w-full rounded-md border border-border bg-background px-2 py-1.5 text-sm"
          />
        </label>
        <label className="text-xs">
          CA
          <input
            type="number"
            min={0}
            value={armorClass}
            onChange={(event) => setArmorClass(event.target.value)}
            className="mt-1 w-full rounded-md border border-border bg-background px-2 py-1.5 text-sm"
          />
        </label>
        <label className="text-xs">
          Iniciativa
          <input
            type="number"
            value={initiative}
            onChange={(event) => setInitiative(event.target.value)}
            className="mt-1 w-full rounded-md border border-border bg-background px-2 py-1.5 text-sm"
          />
        </label>
        <label className="text-xs">
          Ordem de turno
          <input
            type="number"
            value={turnOrder}
            onChange={(event) => setTurnOrder(event.target.value)}
            className="mt-1 w-full rounded-md border border-border bg-background px-2 py-1.5 text-sm"
          />
        </label>
      </div>

      <button
        type="submit"
        className="w-full rounded-md bg-primary px-3 py-2 text-sm font-medium text-primary-foreground hover:opacity-90"
      >
        Adicionar participante
      </button>
    </form>
  );
}
