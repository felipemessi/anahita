"use client";

import { useState } from "react";

import { circleLabel, SpellSearch } from "@/components/characters/spell-search";
import { useCatalogEntry, useCatalogList } from "@/hooks/use-catalog";
import {
  useAddCharacterSpell,
  useCastCharacterSpell,
  useRemoveCharacterSpell,
  useUpdateCharacterSpell,
} from "@/hooks/use-character";
import { ApiError } from "@/lib/api/client";
import type { ClassSummary, SpellSummary } from "@/types/catalog";
import type { CharacterClass, CharacterSpell, CharacterSpellSlot } from "@/types/character";

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
  spellSlots,
}: {
  characterId: string;
  campaignId: string;
  spells: CharacterSpell[];
  classes: CharacterClass[];
  spellSlots: CharacterSpellSlot[];
}) {
  const { data: catalogClasses } = useCatalogList("classes", {
    campaign_id: campaignId,
  });
  const { data: catalogSpells } = useCatalogList("spells", { campaign_id: campaignId });
  const addSpell = useAddCharacterSpell(characterId);
  const updateSpell = useUpdateCharacterSpell(characterId);
  const removeSpell = useRemoveCharacterSpell(characterId);
  const castSpell = useCastCharacterSpell(characterId);
  const [error, setError] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [castLevelBySpell, setCastLevelBySpell] = useState<Record<string, number>>({});
  const [togglingId, setTogglingId] = useState<string | null>(null);

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
    setTogglingId(spell.id);
    try {
      await updateSpell.mutateAsync({
        spellEntryId: spell.id,
        data: { prepared: !spell.prepared },
      });
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Não foi possível preparar a magia.",
      );
    } finally {
      setTogglingId(null);
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

  function availableCastLevels(spellLevel: number): number[] {
    return spellSlots
      .filter((slot) => slot.spell_level >= spellLevel && slot.used < slot.max)
      .map((slot) => slot.spell_level)
      .sort((a, b) => a - b);
  }

  /** The spell's own level if it has a slot, else the lowest level that does. */
  function defaultCastLevel(spell: CharacterSpell): number {
    const available = availableCastLevels(spell.level);
    return available.includes(spell.level) ? spell.level : (available[0] ?? spell.level);
  }

  async function handleCast(spell: CharacterSpell, options: { asRitual?: boolean } = {}) {
    setError(null);
    try {
      await castSpell.mutateAsync({
        spellEntryId: spell.id,
        data: options.asRitual
          ? { as_ritual: true }
          : { cast_at_level: castLevelBySpell[spell.id] ?? defaultCastLevel(spell) },
      });
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Não foi possível conjurar a magia.",
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
                        disabled={togglingId === spell.id}
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
                  {level > 0 ? (
                    <CastControls
                      spell={spell}
                      availableLevels={availableCastLevels(spell.level)}
                      castLevel={castLevelBySpell[spell.id] ?? defaultCastLevel(spell)}
                      onCastLevelChange={(newLevel) =>
                        setCastLevelBySpell((prev) => ({ ...prev, [spell.id]: newLevel }))
                      }
                      onCast={() => handleCast(spell)}
                      onCastAsRitual={
                        spell.ritual ? () => handleCast(spell, { asRitual: true }) : undefined
                      }
                      isPending={castSpell.isPending}
                    />
                  ) : null}
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

/**
 * Cast controls for one non-cantrip spell: a level selector (only when more
 * than one slot level is available, for upcasting), a "conjurar" button
 * (disabled with an explanatory tooltip when no slot is available), and a
 * "conjurar como ritual" button when the spell allows it (never disabled —
 * a ritual cast never consumes a slot).
 */
function CastControls({
  spell,
  availableLevels,
  castLevel,
  onCastLevelChange,
  onCast,
  onCastAsRitual,
  isPending,
}: {
  spell: CharacterSpell;
  availableLevels: number[];
  castLevel: number;
  onCastLevelChange: (level: number) => void;
  onCast: () => void;
  onCastAsRitual?: () => void;
  isPending: boolean;
}) {
  const hasSlot = availableLevels.length > 0;

  return (
    <div className="mt-1 flex items-center gap-2 text-xs">
      {availableLevels.length > 1 ? (
        <select
          value={castLevel}
          onChange={(e) => onCastLevelChange(Number(e.target.value))}
          aria-label={`Nível de conjuração de ${spell.spell_id}`}
          className="rounded-md border border-input bg-background px-1 py-0.5 text-xs"
        >
          {availableLevels.map((level) => (
            <option key={level} value={level}>
              {circleLabel(level)}
            </option>
          ))}
        </select>
      ) : null}
      <button
        type="button"
        onClick={onCast}
        disabled={!hasSlot || isPending}
        title={hasSlot ? undefined : "Nenhum slot disponível"}
        className="rounded border border-border px-2 py-0.5 hover:bg-secondary disabled:opacity-40"
      >
        conjurar
      </button>
      {onCastAsRitual ? (
        <button
          type="button"
          onClick={onCastAsRitual}
          disabled={isPending}
          className="rounded border border-border px-2 py-0.5 hover:bg-secondary disabled:opacity-40"
        >
          conjurar como ritual
        </button>
      ) : null}
    </div>
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
