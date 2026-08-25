"use client";

import { useState } from "react";

import { circleLabel, SpellSearch } from "@/components/characters/spell-search";
import { useCatalogEntry, useCatalogList } from "@/hooks/use-catalog";
import {
  useAddCharacterSpell,
  useRemoveCharacterSpell,
  useUpdateCharacterSpell,
} from "@/hooks/use-character";
import { ApiError } from "@/lib/api/client";
import type { ClassSummary, SpellSummary } from "@/types/catalog";
import type { CharacterClass, CharacterSpell } from "@/types/character";

/**
 * Known spells grouped by circle (0 = truques), with prepare/unprepare,
 * remove, an expandable detail, and a search to add another — replaces the
 * old flat list + single-select `spell-slots.tsx` used to be (that file now
 * shows numeric slot counters instead, see `spell-slots.tsx`).
 */
export function SpellListByCircle({
  characterId,
  campaignId,
  spells,
  classes,
}: {
  characterId: string;
  campaignId: string;
  spells: CharacterSpell[];
  classes: CharacterClass[];
}) {
  const { data: catalogClasses } = useCatalogList("classes", {
    campaign_id: campaignId,
  });
  const { data: catalogSpells } = useCatalogList("spells", { campaign_id: campaignId });
  const addSpell = useAddCharacterSpell(characterId);
  const updateSpell = useUpdateCharacterSpell(characterId);
  const removeSpell = useRemoveCharacterSpell(characterId);
  const [error, setError] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const classOptions = classes
    .map((c) => catalogClasses?.find((cc) => cc.id === c.class_definition_id))
    .filter((c): c is ClassSummary => Boolean(c));
  const [sourceClassIndex, setSourceClassIndex] = useState<string | null>(null);
  const activeClassIndex = sourceClassIndex ?? classOptions[0]?.index ?? null;

  function nameFor(spellId: string): string {
    return catalogSpells?.find((s) => s.id === spellId)?.name ?? spellId;
  }

  const grouped = new Map<number, CharacterSpell[]>();
  for (const spell of spells) {
    const list = grouped.get(spell.level) ?? [];
    list.push(spell);
    grouped.set(spell.level, list);
  }
  const circles = [...grouped.keys()].sort((a, b) => a - b);

  async function handleAdd(spell: SpellSummary) {
    setError(null);
    try {
      await addSpell.mutateAsync({
        spell_id: spell.id,
        source_class: activeClassIndex,
      });
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Não foi possível adicionar a magia.",
      );
    }
  }

  async function handleTogglePrepared(spell: CharacterSpell) {
    setError(null);
    try {
      await updateSpell.mutateAsync({
        spellEntryId: spell.id,
        data: { prepared: !spell.prepared },
      });
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Não foi possível preparar a magia.",
      );
    }
  }

  async function handleRemove(spell: CharacterSpell) {
    setError(null);
    try {
      await removeSpell.mutateAsync(spell.id);
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Não foi possível remover a magia.",
      );
    }
  }

  return (
    <section aria-label="Magias" className="space-y-4 rounded-lg border border-border bg-card p-4">
      <h2 className="font-semibold">Magias</h2>

      {circles.length === 0 ? (
        <p className="text-sm text-muted-foreground">Nenhuma magia conhecida.</p>
      ) : (
        circles.map((level) => (
          <div key={level}>
            <h3 className="text-xs font-semibold uppercase text-muted-foreground">
              {circleLabel(level)}
            </h3>
            <ul className="mt-1 divide-y divide-border">
              {grouped.get(level)?.map((spell) => (
                <li key={spell.id} className="py-2">
                  <div className="flex items-center justify-between gap-2">
                    <button
                      type="button"
                      onClick={() =>
                        setExpandedId(expandedId === spell.id ? null : spell.id)
                      }
                      className="text-left text-sm hover:underline"
                    >
                      {nameFor(spell.spell_id)}
                      {spell.ritual ? (
                        <span className="ml-1 text-xs text-muted-foreground">
                          (ritual)
                        </span>
                      ) : null}
                    </button>
                    <div className="flex items-center gap-2 text-xs">
                      <button
                        type="button"
                        onClick={() => handleTogglePrepared(spell)}
                        disabled={updateSpell.isPending}
                        className={
                          spell.prepared
                            ? "text-primary hover:underline"
                            : "text-muted-foreground hover:underline"
                        }
                      >
                        {spell.prepared ? "preparada" : "preparar"}
                      </button>
                      <button
                        type="button"
                        onClick={() => handleRemove(spell)}
                        disabled={removeSpell.isPending}
                        className="text-destructive hover:underline"
                      >
                        remover
                      </button>
                    </div>
                  </div>
                  {expandedId === spell.id ? <SpellDetail spellId={spell.spell_id} /> : null}
                </li>
              ))}
            </ul>
          </div>
        ))
      )}

      <div className="space-y-2 border-t border-border pt-3">
        <p className="text-xs text-muted-foreground">Adicionar magia</p>
        {classOptions.length > 1 ? (
          <select
            value={activeClassIndex ?? ""}
            onChange={(e) => setSourceClassIndex(e.target.value)}
            aria-label="Classe conjuradora"
            className="rounded-md border border-input bg-background px-2 py-1.5 text-sm"
          >
            {classOptions.map((c) => (
              <option key={c.id} value={c.index ?? ""}>
                {c.name}
              </option>
            ))}
          </select>
        ) : null}
        <SpellSearch
          campaignId={campaignId}
          classIndex={activeClassIndex}
          excludeSpellIds={new Set(spells.map((s) => s.spell_id))}
          onSelect={handleAdd}
        />
      </div>

      {error ? (
        <p role="alert" className="text-sm text-destructive">
          {error}
        </p>
      ) : null}
    </section>
  );
}

function SpellDetail({ spellId }: { spellId: string }) {
  const { data: spell, isLoading } = useCatalogEntry("spells", spellId);
  if (isLoading || !spell) {
    return <p className="mt-1 text-xs text-muted-foreground">Carregando…</p>;
  }
  return (
    <div className="mt-1 space-y-1 text-xs text-muted-foreground">
      <p>
        {spell.casting_time} · {spell.range} · {spell.duration} · {spell.components}
      </p>
      <p>{spell.description}</p>
    </div>
  );
}
