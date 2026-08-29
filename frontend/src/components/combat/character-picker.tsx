"use client";

import { useEffect, useState } from "react";

import { useCharacters } from "@/hooks/use-character";
import { useCombat } from "@/hooks/use-combat";
import { isFullCharacter } from "@/types/character";

/**
 * Add-participant form: pick one of the campaign's player characters to
 * autocomplete name/HP/AC from their sheet. Unlike `MonsterPicker` there's
 * no manual-entry fallback — a character participant always carries
 * `character_id`, and the sheet is the source of truth for its stats.
 * Initiative and turn order stay manual, same as `MonsterPicker`.
 */
export function CharacterPicker({ campaignId }: { campaignId: string }) {
  const { addParticipant } = useCombat();
  const { data: characters } = useCharacters(campaignId);

  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [hitPointMax, setHitPointMax] = useState("");
  const [armorClass, setArmorClass] = useState("");
  const [initiative, setInitiative] = useState("");
  const [turnOrder, setTurnOrder] = useState("");

  const selected = characters?.find((c) => c.id === selectedId);

  // Autofill name/HP/AC once a character with a full sheet is selected.
  useEffect(() => {
    if (!selected || !isFullCharacter(selected)) return;
    setName(selected.name);
    setHitPointMax(String(selected.hit_point_max));
    setArmorClass(String(selected.armor_class));
  }, [selected]);

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    const hp = Number(hitPointMax);
    const ac = Number(armorClass);
    const init = Number(initiative);
    const order = Number(turnOrder);
    if (!selectedId) return;
    if (!name.trim() || !Number.isFinite(hp) || hp < 1) return;
    if (!Number.isFinite(ac) || ac < 0) return;
    if (!Number.isFinite(init) || !Number.isFinite(order)) return;

    addParticipant({
      npc_id: null,
      character_id: selectedId,
      name: name.trim(),
      hit_point_max: hp,
      armor_class: ac,
      initiative: init,
      turn_order: order,
    });

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
        <label htmlFor="character-picker-select" className="text-xs text-muted-foreground">
          Selecionar personagem
        </label>
        <select
          id="character-picker-select"
          value={selectedId ?? ""}
          onChange={(event) => setSelectedId(event.target.value || null)}
          className="mt-1 w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
        >
          <option value="">— Escolha um personagem —</option>
          {characters?.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>
      </div>

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
        disabled={!selectedId}
        className="w-full rounded-md bg-primary px-3 py-2 text-sm font-medium text-primary-foreground hover:opacity-90 disabled:opacity-50"
      >
        Adicionar participante
      </button>
    </form>
  );
}
