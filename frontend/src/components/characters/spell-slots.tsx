"use client";

import { useState, type FormEvent } from "react";

import { useCatalogList } from "@/hooks/use-catalog";
import { useAddCharacterSpell } from "@/hooks/use-character";
import type { CharacterSpell } from "@/types/character";

/** Known/prepared spells, with a form to add another from the campaign catalog. */
export function SpellSlots({
  characterId,
  campaignId,
  spells,
}: {
  characterId: string;
  campaignId: string;
  spells: CharacterSpell[];
}) {
  const { data: catalogSpells } = useCatalogList("spells", { campaign_id: campaignId });
  const addSpell = useAddCharacterSpell(characterId);
  const [spellId, setSpellId] = useState("");
  const [prepared, setPrepared] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function nameFor(id: string): string {
    return catalogSpells?.find((s) => s.id === id)?.name ?? id;
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!spellId) return;
    setError(null);
    try {
      await addSpell.mutateAsync({ spell_id: spellId, prepared });
      setSpellId("");
      setPrepared(false);
    } catch {
      setError("Não foi possível adicionar a magia.");
    }
  }

  return (
    <section aria-label="Magias" className="rounded-lg border border-border bg-card p-4">
      <h3 className="font-semibold">Magias</h3>

      {spells.length > 0 ? (
        <ul className="mt-2 space-y-1 text-sm">
          {spells.map((spell) => (
            <li key={spell.id} className="flex items-center justify-between">
              <span>{nameFor(spell.spell_id)}</span>
              {spell.prepared ? (
                <span className="text-xs text-primary">preparada</span>
              ) : null}
            </li>
          ))}
        </ul>
      ) : (
        <p className="mt-1 text-sm text-muted-foreground">Nenhuma magia conhecida.</p>
      )}

      <form onSubmit={handleSubmit} className="mt-3 flex flex-wrap items-end gap-3">
        <div className="space-y-1">
          <label htmlFor="add-spell" className="text-xs text-muted-foreground">
            Adicionar magia
          </label>
          <select
            id="add-spell"
            value={spellId}
            onChange={(e) => setSpellId(e.target.value)}
            className="rounded-md border border-input bg-background px-2 py-1.5 text-sm"
          >
            <option value="">Selecione…</option>
            {catalogSpells?.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
        </div>
        <label className="flex items-center gap-1 text-xs text-muted-foreground">
          <input
            type="checkbox"
            checked={prepared}
            onChange={(e) => setPrepared(e.target.checked)}
          />
          Preparada
        </label>
        <button
          type="submit"
          disabled={!spellId || addSpell.isPending}
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
