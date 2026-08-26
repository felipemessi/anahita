"use client";

import { useState } from "react";

import { useShowServerRoll } from "@/components/characters/roll-log";
import { useCatalogList } from "@/hooks/use-catalog";
import { useRestCharacter } from "@/hooks/use-character";
import { ApiError } from "@/lib/api/client";
import type { CharacterClass } from "@/types/character";

/**
 * Hit dice available/spent per class (same dot-indicator pattern as
 * `spell-slots.tsx`), with a "gastar dado de vida" control that takes a
 * short rest spending the chosen count — resolved server-side (roll +
 * CON modifier, capped at `hit_point_max`).
 */
export function HitDiceTracker({
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
  const rest = useRestCharacter(characterId);
  const showServerRoll = useShowServerRoll();
  const [countByClass, setCountByClass] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);

  if (classes.length === 0) return null;

  function nameFor(classEntry: CharacterClass): string {
    return catalogClasses?.find((c) => c.id === classEntry.class_definition_id)?.name ?? "Classe";
  }

  async function handleSpend(classEntry: CharacterClass) {
    const count = Number(countByClass[classEntry.id] ?? "1");
    if (!count || count <= 0) return;
    setError(null);
    try {
      const { hit_dice_rolls } = await rest.mutateAsync({
        rest_type: "short",
        hit_dice_spent: [{ character_class_id: classEntry.id, count }],
      });
      const rolled = hit_dice_rolls[0];
      if (rolled) {
        showServerRoll({
          label: `Dado de vida (${nameFor(classEntry)})`,
          rollResult: rolled.roll_result,
          modifier: rolled.modifier,
          total: rolled.healed,
        });
      }
      setCountByClass((prev) => ({ ...prev, [classEntry.id]: "1" }));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Não foi possível gastar o dado de vida.");
    }
  }

  return (
    <section aria-label="Dados de vida" className="rounded-lg border border-border bg-card p-4">
      <h2 className="font-semibold">Dados de vida</h2>
      <ul className="mt-2 space-y-2">
        {classes.map((classEntry) => {
          const available = classEntry.level - classEntry.hit_dice_used;
          return (
            <li key={classEntry.id} className="flex flex-wrap items-center gap-2 text-sm">
              <span className="w-24 text-xs text-muted-foreground">{nameFor(classEntry)}</span>
              <span
                aria-label={`${available} de ${classEntry.level} dados de vida disponíveis`}
                className="font-mono tracking-widest"
              >
                {Array.from({ length: classEntry.level }, (_, i) =>
                  i < available ? "●" : "○",
                ).join(" ")}
              </span>
              <span className="text-xs text-muted-foreground">
                {available}/{classEntry.level}
              </span>
              <input
                type="number"
                min={1}
                max={Math.max(1, available)}
                value={countByClass[classEntry.id] ?? "1"}
                onChange={(e) =>
                  setCountByClass((prev) => ({ ...prev, [classEntry.id]: e.target.value }))
                }
                disabled={available === 0}
                aria-label={`Quantidade de dados de vida a gastar de ${nameFor(classEntry)}`}
                className="w-14 rounded-md border border-input bg-background px-2 py-1 text-sm disabled:opacity-40"
              />
              <button
                type="button"
                onClick={() => handleSpend(classEntry)}
                disabled={available === 0 || rest.isPending}
                className="rounded-md border border-border px-3 py-1 text-xs hover:bg-secondary disabled:opacity-40"
              >
                Gastar dado de vida
              </button>
            </li>
          );
        })}
      </ul>
      {error ? (
        <p role="alert" className="mt-2 text-sm text-destructive">
          {error}
        </p>
      ) : null}
    </section>
  );
}
