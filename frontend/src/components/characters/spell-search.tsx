"use client";

import { useState } from "react";

import { useCatalogList } from "@/hooks/use-catalog";
import type { SpellSummary } from "@/types/catalog";

/** `0` = "Truques", others "Nº círculo" — matches the sheet's grouping labels. */
export function circleLabel(level: number): string {
  return level === 0 ? "Truques" : `${level}º círculo`;
}

/**
 * Search the campaign's spell catalog by name/circle, narrowed to `classIndex`
 * (the character's own casting class) by default — a checkbox lets the
 * user drop that filter and search every class's spells instead. Each
 * result shows which classes can cast it (e.g. "Cleric/Druid"), reusing the
 * same `useCatalogList("spells", …)` + filter-bar pattern as
 * `catalog-filter-bar.tsx`.
 */
export function SpellSearch({
  campaignId,
  classIndex,
  excludeSpellIds,
  onSelect,
}: {
  campaignId: string;
  classIndex: string | null;
  excludeSpellIds: Set<string>;
  onSelect: (spell: SpellSummary) => void;
}) {
  const [name, setName] = useState("");
  const [level, setLevel] = useState("");
  const [showAllClasses, setShowAllClasses] = useState(false);

  const { data: spells, isLoading } = useCatalogList("spells", {
    campaign_id: campaignId,
    ...(classIndex && !showAllClasses ? { class_index: classIndex } : {}),
    ...(level !== "" ? { level: Number(level) } : {}),
    ...(name ? { search: name } : {}),
  });

  const results = (spells ?? []).filter((spell) => !excludeSpellIds.has(spell.id));

  return (
    <div className="space-y-2">
      <div className="flex flex-wrap gap-2">
        <input
          type="search"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Buscar magia por nome…"
          aria-label="Buscar magia por nome"
          className="min-w-0 flex-1 rounded-md border border-input bg-background px-2 py-1.5 text-sm"
        />
        <select
          value={level}
          onChange={(e) => setLevel(e.target.value)}
          aria-label="Filtrar por círculo"
          className="rounded-md border border-input bg-background px-2 py-1.5 text-sm"
        >
          <option value="">Todos os círculos</option>
          {Array.from({ length: 10 }, (_, level) => level).map((level) => (
            <option key={level} value={level}>
              {circleLabel(level)}
            </option>
          ))}
        </select>
      </div>

      {classIndex ? (
        <label className="flex items-center gap-1.5 text-xs text-muted-foreground">
          <input
            type="checkbox"
            checked={showAllClasses}
            onChange={(e) => setShowAllClasses(e.target.checked)}
          />
          Mostrar magias de todas as classes
        </label>
      ) : null}

      {isLoading ? (
        <p className="text-xs text-muted-foreground">Carregando…</p>
      ) : results.length === 0 ? (
        <p className="text-xs text-muted-foreground">Nenhuma magia encontrada.</p>
      ) : (
        <ul className="max-h-48 divide-y divide-border overflow-y-auto rounded-md border border-border">
          {results.map((spell) => (
            <li key={spell.id}>
              <button
                type="button"
                onClick={() => onSelect(spell)}
                className="flex w-full items-center justify-between gap-2 px-2 py-1.5 text-left text-sm hover:bg-secondary/40"
              >
                <span className="min-w-0 flex-1 truncate">
                  {spell.name}
                  {spell.ritual ? (
                    <span className="ml-1 text-xs text-muted-foreground">(ritual)</span>
                  ) : null}
                </span>
                {spell.classes.length > 0 ? (
                  <span className="shrink-0 text-xs text-muted-foreground">
                    {spell.classes.map((c) => c.name).join("/")}
                  </span>
                ) : null}
                <span className="shrink-0 text-xs text-muted-foreground">
                  {circleLabel(spell.level)}
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
