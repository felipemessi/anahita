"use client";

import { useState } from "react";

import { useCatalogEntry, useCatalogList } from "@/hooks/use-catalog";
import { useLevelUpCharacter } from "@/hooks/use-character";
import { ApiError } from "@/lib/api/client";
import type { AbilityScore } from "@/types/catalog";
import type { CharacterClass } from "@/types/character";

const ABILITY_LABELS: Record<AbilityScore, string> = {
  str: "Força",
  dex: "Destreza",
  con: "Constituição",
  int: "Inteligência",
  wis: "Sabedoria",
  cha: "Carisma",
};
const ABILITIES = Object.keys(ABILITY_LABELS) as AbilityScore[];

type AsiMode = "plus-two" | "plus-one-plus-one" | "feat";

/** `existing:<CharacterClass.id>` or `new:<catalog class_definition_id>`. */
type Selection = { kind: "existing"; characterClassId: string } | { kind: "new"; classDefinitionId: string };

function parseSelection(value: string): Selection | null {
  const [kind, id] = value.split(":");
  if (!id) return null;
  if (kind === "existing") return { kind: "existing", characterClassId: id };
  if (kind === "new") return { kind: "new", classDefinitionId: id };
  return null;
}

/**
 * Guided level-up flow: pick which class to level up — or, via a second
 * option group, a brand-new class the character doesn't have yet
 * (multiclassing in at level 1) — and, only at a level that grants an
 * ability score improvement (`ClassLevel`'s `ability_score_bonuses`,
 * resolved from the catalog) — choose between distributing +2 (one
 * ability) / +1+1 (two abilities) or a catalog feat. HP gained is rolled
 * server-side; shown after the fact rather than confirmed beforehand, same
 * "let the server roll" convention as rest.
 */
export function LevelUpDialog({
  characterId,
  campaignId,
  classes,
}: {
  characterId: string;
  campaignId: string;
  classes: CharacterClass[];
}) {
  const { data: catalogClasses } = useCatalogList("classes", {
    campaign_id: campaignId,
  });
  const { data: catalogFeats } = useCatalogList("feats", { campaign_id: campaignId });
  const levelUp = useLevelUpCharacter(characterId);

  const [open, setOpen] = useState(false);
  const [selection, setSelection] = useState(
    classes[0] ? `existing:${classes[0].id}` : "",
  );
  const [asiMode, setAsiMode] = useState<AsiMode>("plus-two");
  const [abilityA, setAbilityA] = useState<AbilityScore>("str");
  const [abilityB, setAbilityB] = useState<AbilityScore>("dex");
  const [featId, setFeatId] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<string | null>(null);

  const parsed = parseSelection(selection);
  const selectedClass =
    parsed?.kind === "existing"
      ? classes.find((c) => c.id === parsed.characterClassId)
      : undefined;
  const classDefinitionId =
    parsed?.kind === "existing"
      ? (selectedClass?.class_definition_id ?? null)
      : (parsed?.classDefinitionId ?? null);
  const { data: catalogClassDetail } = useCatalogEntry("classes", classDefinitionId ?? "");
  const nextLevel = (selectedClass?.level ?? 0) + 1;
  const isAsiLevel =
    catalogClassDetail?.levels.find((l) => l.level === nextLevel)?.ability_score_bonuses !=
    null;

  const ownedClassDefIds = new Set(classes.map((c) => c.class_definition_id));
  const newClassOptions = catalogClasses?.filter((c) => !ownedClassDefIds.has(c.id)) ?? [];

  function nameFor(classEntry: CharacterClass): string {
    return catalogClasses?.find((c) => c.id === classEntry.class_definition_id)?.name ?? "Classe";
  }

  async function handleSubmit() {
    if (!classDefinitionId) return;
    setError(null);
    setResult(null);
    try {
      const character = await levelUp.mutateAsync({
        class_definition_id: classDefinitionId,
        ability_score_increases:
          isAsiLevel && asiMode !== "feat"
            ? asiMode === "plus-two"
              ? { [abilityA]: 2 }
              : { [abilityA]: 1, [abilityB]: 1 }
            : undefined,
        feat_id: isAsiLevel && asiMode === "feat" ? featId : undefined,
      });
      const label =
        parsed?.kind === "existing" && selectedClass
          ? nameFor(selectedClass)
          : (catalogClasses?.find((c) => c.id === classDefinitionId)?.name ?? "Classe");
      setResult(
        `${label} agora está no nível ${nextLevel}. PV máximo: ${character.hit_point_max}.`,
      );
      setOpen(false);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Não foi possível subir de nível.");
    }
  }

  if (classes.length === 0) return null;

  return (
    <section aria-label="Subir de nível" className="rounded-lg border border-border bg-card p-4">
      <div className="flex items-center justify-between">
        <h2 className="font-semibold">Subir de nível</h2>
        <button
          type="button"
          onClick={() => setOpen((v) => !v)}
          className="text-sm text-primary underline"
        >
          {open ? "Cancelar" : "Subir de nível"}
        </button>
      </div>

      {result ? <p className="mt-2 text-sm text-emerald-500">{result}</p> : null}

      {open ? (
        <div className="mt-3 space-y-3">
          <div className="space-y-1">
            <label htmlFor="level-up-class" className="text-xs text-muted-foreground">
              Classe
            </label>
            <select
              id="level-up-class"
              value={selection}
              onChange={(e) => setSelection(e.target.value)}
              className="w-full rounded-md border border-input bg-background px-2 py-1.5 text-sm"
            >
              <optgroup label="Subir nível">
                {classes.map((c) => (
                  <option key={c.id} value={`existing:${c.id}`}>
                    {nameFor(c)} (nível {c.level} → {c.level + 1})
                  </option>
                ))}
              </optgroup>
              {newClassOptions.length > 0 ? (
                <optgroup label="Multiclasse — adicionar uma nova classe">
                  {newClassOptions.map((c) => (
                    <option key={c.id} value={`new:${c.id}`}>
                      {c.name} (nova, nível 1)
                    </option>
                  ))}
                </optgroup>
              ) : null}
            </select>
          </div>

          {isAsiLevel ? (
            <div className="space-y-2 rounded-md border border-border p-3">
              <p className="text-xs font-medium">
                Nível {nextLevel} concede melhoria de habilidade ou talento
              </p>
              <select
                aria-label="Tipo de melhoria"
                value={asiMode}
                onChange={(e) => setAsiMode(e.target.value as AsiMode)}
                className="w-full rounded-md border border-input bg-background px-2 py-1.5 text-sm"
              >
                <option value="plus-two">+2 numa habilidade</option>
                <option value="plus-one-plus-one">+1 em duas habilidades</option>
                <option value="feat">Talento</option>
              </select>

              {asiMode !== "feat" ? (
                <div className="flex items-center gap-2">
                  <select
                    aria-label="Primeira habilidade"
                    value={abilityA}
                    onChange={(e) => setAbilityA(e.target.value as AbilityScore)}
                    className="rounded-md border border-input bg-background px-2 py-1.5 text-sm"
                  >
                    {ABILITIES.map((a) => (
                      <option key={a} value={a}>
                        {ABILITY_LABELS[a]}
                      </option>
                    ))}
                  </select>
                  {asiMode === "plus-one-plus-one" ? (
                    <select
                      aria-label="Segunda habilidade"
                      value={abilityB}
                      onChange={(e) => setAbilityB(e.target.value as AbilityScore)}
                      className="rounded-md border border-input bg-background px-2 py-1.5 text-sm"
                    >
                      {ABILITIES.map((a) => (
                        <option key={a} value={a}>
                          {ABILITY_LABELS[a]}
                        </option>
                      ))}
                    </select>
                  ) : null}
                </div>
              ) : (
                <select
                  aria-label="Talento"
                  value={featId}
                  onChange={(e) => setFeatId(e.target.value)}
                  className="w-full rounded-md border border-input bg-background px-2 py-1.5 text-sm"
                >
                  <option value="">Selecione um talento</option>
                  {catalogFeats?.map((feat) => (
                    <option key={feat.id} value={feat.id}>
                      {feat.name}
                    </option>
                  ))}
                </select>
              )}
            </div>
          ) : null}

          <button
            type="button"
            onClick={handleSubmit}
            disabled={
              levelUp.isPending || (isAsiLevel && asiMode === "feat" && !featId)
            }
            className="rounded-md border border-border px-3 py-1.5 text-sm hover:bg-secondary disabled:opacity-40"
          >
            Confirmar
          </button>
        </div>
      ) : null}

      {error ? (
        <p role="alert" className="mt-2 text-sm text-destructive">
          {error}
        </p>
      ) : null}
    </section>
  );
}
