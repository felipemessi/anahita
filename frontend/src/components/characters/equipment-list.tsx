"use client";

import { useState, type FormEvent } from "react";

import { useRoll, useRollDamage } from "@/components/characters/roll-log";
import { useCatalogEntry, useCatalogList } from "@/hooks/use-catalog";
import {
  useAddCharacterEquipment,
  useRemoveCharacterEquipment,
  useUpdateCharacterEquipment,
  useWeaponAttackProfile,
} from "@/hooks/use-character";
import { ApiError } from "@/lib/api/client";
import type { CharacterEquipment } from "@/types/character";

/**
 * A character's personal inventory: toggle equipped/attunement, edit
 * quantity, remove, an expandable detail, and a form to add another item
 * from the campaign catalog — replaces the inline equipment section that
 * used to live directly in `character-sheet.tsx`.
 */
export function EquipmentList({
  characterId,
  campaignId,
  equipment,
}: {
  characterId: string;
  campaignId: string;
  equipment: CharacterEquipment[];
}) {
  const { data: catalogItems } = useCatalogList("equipment", { campaign_id: campaignId });
  const addEquipment = useAddCharacterEquipment(characterId);
  const updateEquipment = useUpdateCharacterEquipment(characterId);
  const removeEquipment = useRemoveCharacterEquipment(characterId);
  const [itemId, setItemId] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  function nameFor(id: string): string {
    return catalogItems?.find((i) => i.id === id)?.name ?? id;
  }

  async function handleAdd(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!itemId) return;
    setError(null);
    try {
      await addEquipment.mutateAsync({ item_id: itemId });
      setItemId("");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Não foi possível adicionar o item.");
    }
  }

  async function handleToggle(entry: CharacterEquipment, field: "equipped" | "attunement") {
    setError(null);
    try {
      await updateEquipment.mutateAsync({
        equipmentId: entry.id,
        data: { [field]: !entry[field] },
      });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Não foi possível atualizar o item.");
    }
  }

  async function handleQuantityChange(entry: CharacterEquipment, quantity: number) {
    if (quantity < 1) return;
    setError(null);
    try {
      await updateEquipment.mutateAsync({ equipmentId: entry.id, data: { quantity } });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Não foi possível atualizar a quantidade.");
    }
  }

  async function handleRemove(entry: CharacterEquipment) {
    setError(null);
    try {
      await removeEquipment.mutateAsync(entry.id);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Não foi possível remover o item.");
    }
  }

  return (
    <section aria-label="Equipamento" className="rounded-lg border border-border bg-card p-4">
      <h2 className="font-semibold">Equipamento</h2>

      {equipment.length > 0 ? (
        <ul className="mt-2 divide-y divide-border">
          {equipment.map((entry) => (
            <li key={entry.id} className="py-2">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <button
                  type="button"
                  onClick={() => setExpandedId(expandedId === entry.id ? null : entry.id)}
                  className="text-left text-sm hover:underline"
                >
                  {nameFor(entry.item_id)}
                </button>
                <div className="flex items-center gap-2 text-xs">
                  <label className="flex items-center gap-1 text-muted-foreground">
                    <span>qtd.</span>
                    <input
                      type="number"
                      min={1}
                      value={entry.quantity}
                      onChange={(e) => handleQuantityChange(entry, Number(e.target.value))}
                      className="w-12 rounded border border-input bg-background px-1 py-0.5"
                    />
                  </label>
                  {entry.equipped ? (
                    <WeaponAttackButton
                      characterId={characterId}
                      equipmentId={entry.id}
                      itemId={entry.item_id}
                      onError={setError}
                    />
                  ) : null}
                  <button
                    type="button"
                    onClick={() => handleToggle(entry, "equipped")}
                    disabled={updateEquipment.isPending}
                    className={
                      entry.equipped ? "text-primary hover:underline" : "text-muted-foreground hover:underline"
                    }
                  >
                    {entry.equipped ? "equipado" : "equipar"}
                  </button>
                  <button
                    type="button"
                    onClick={() => handleToggle(entry, "attunement")}
                    disabled={updateEquipment.isPending}
                    className={
                      entry.attunement
                        ? "text-primary hover:underline"
                        : "text-muted-foreground hover:underline"
                    }
                  >
                    {entry.attunement ? "sintonizado" : "sintonizar"}
                  </button>
                  <button
                    type="button"
                    onClick={() => handleRemove(entry)}
                    disabled={removeEquipment.isPending}
                    className="text-destructive hover:underline"
                  >
                    remover
                  </button>
                </div>
              </div>
              {expandedId === entry.id ? <ItemDetail itemId={entry.item_id} /> : null}
            </li>
          ))}
        </ul>
      ) : (
        <p className="mt-1 text-sm text-muted-foreground">Inventário vazio.</p>
      )}

      <form onSubmit={handleAdd} className="mt-3 flex flex-wrap items-end gap-3">
        <div className="space-y-1">
          <label htmlFor="add-item" className="text-xs text-muted-foreground">
            Adicionar item
          </label>
          <select
            id="add-item"
            value={itemId}
            onChange={(e) => setItemId(e.target.value)}
            className="rounded-md border border-input bg-background px-2 py-1.5 text-sm"
          >
            <option value="">Selecione…</option>
            {catalogItems?.map((i) => (
              <option key={i.id} value={i.id}>
                {i.name}
              </option>
            ))}
          </select>
        </div>
        <button
          type="submit"
          disabled={!itemId || addEquipment.isPending}
          className="rounded-md border border-border px-3 py-1.5 text-sm hover:bg-secondary disabled:opacity-40"
        >
          Adicionar
        </button>
      </form>
      {error ? (
        <p role="alert" className="mt-1 text-sm text-destructive">
          {error}
        </p>
      ) : null}
    </section>
  );
}

/**
 * "Atacar" / "Dano" for an equipped weapon, straight from the sheet (no
 * combat encounter needed) — resolved by `GET .../attack-profile`, same
 * ability/proficiency math the combat tracker uses. Two separate buttons,
 * each rolled by hand: damage is never rolled automatically after the
 * attack, since whether it even lands is for the table to call. Renders
 * nothing for a non-weapon item.
 */
function WeaponAttackButton({
  characterId,
  equipmentId,
  itemId,
  onError,
}: {
  characterId: string;
  equipmentId: string;
  itemId: string;
  onError: (message: string | null) => void;
}) {
  const { data: item } = useCatalogEntry("equipment", itemId);
  const attackProfile = useWeaponAttackProfile(characterId);
  const roll = useRoll();
  const rollDamage = useRollDamage();

  if (!item?.weapon_detail) return null;

  async function handleRoll(kind: "attack" | "damage") {
    onError(null);
    try {
      const profile = await attackProfile.mutateAsync(equipmentId);
      if (kind === "attack") {
        roll(`${profile.weapon_name} (ataque)`, profile.attack_bonus);
      } else {
        rollDamage(
          `${profile.weapon_name} (dano)`,
          profile.damage_dice,
          profile.damage_bonus,
        );
      }
    } catch (err) {
      onError(err instanceof ApiError ? err.message : "Não foi possível atacar.");
    }
  }

  return (
    <>
      <button
        type="button"
        onClick={() => handleRoll("attack")}
        disabled={attackProfile.isPending}
        className="text-primary hover:underline disabled:opacity-40"
      >
        atacar
      </button>
      <button
        type="button"
        onClick={() => handleRoll("damage")}
        disabled={attackProfile.isPending}
        className="text-primary hover:underline disabled:opacity-40"
      >
        dano
      </button>
    </>
  );
}

function ItemDetail({ itemId }: { itemId: string }) {
  const { data: item, isLoading } = useCatalogEntry("equipment", itemId);
  if (isLoading || !item) {
    return <p className="mt-1 text-xs text-muted-foreground">Carregando…</p>;
  }
  return (
    <div className="mt-1 space-y-1 text-xs text-muted-foreground">
      <p>{item.description || "Sem descrição."}</p>
    </div>
  );
}
