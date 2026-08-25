"use client";

import { useState } from "react";

import { useSpendCharacterResource } from "@/hooks/use-character";
import { ApiError } from "@/lib/api/client";
import type { CharacterResource } from "@/types/character";

/** Mirrors `CharacterService._RESOURCE_RECHARGE`'s keys, for display only. */
const RESOURCE_LABEL: Record<string, string> = {
  rage_count: "Fúria",
  ki_points: "Pontos de ki",
  sorcery_points: "Pontos de feitiçaria",
  action_surges: "Surto de ação",
  channel_divinity_charges: "Canalizar divindade",
  indomitable_uses: "Indomável",
  bardic_inspiration_die: "Inspiração de bardo",
};

/**
 * A character's trackable class resources (rage, ki, ...) with a "usar"
 * button per resource, disabled at the limit — restored by a short or
 * long rest (`HitDiceTracker`'s "gastar dado de vida"/the sheet's
 * "descanso curto"/"descanso longo" buttons), depending on each
 * resource's own recharge type, already handled server-side.
 */
export function ClassResources({
  characterId,
  resources,
}: {
  characterId: string;
  resources: CharacterResource[];
}) {
  const spend = useSpendCharacterResource(characterId);
  const [error, setError] = useState<string | null>(null);

  if (resources.length === 0) return null;

  async function handleUse(resourceKey: string) {
    setError(null);
    try {
      await spend.mutateAsync(resourceKey);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Não foi possível usar o recurso.");
    }
  }

  return (
    <section
      aria-label="Recursos de classe"
      className="rounded-lg border border-border bg-card p-4"
    >
      <h2 className="font-semibold">Recursos de classe</h2>
      <ul className="mt-2 space-y-2">
        {resources.map((resource) => {
          const available = resource.max - resource.used;
          return (
            <li
              key={resource.resource_key}
              className="flex items-center justify-between gap-2 text-sm"
            >
              <span>{RESOURCE_LABEL[resource.resource_key] ?? resource.resource_key}</span>
              <div className="flex items-center gap-2">
                <span className="font-mono text-xs text-muted-foreground">
                  {available}/{resource.max}
                </span>
                <button
                  type="button"
                  onClick={() => handleUse(resource.resource_key)}
                  disabled={available === 0 || spend.isPending}
                  className="rounded-md border border-border px-3 py-1 text-xs hover:bg-secondary disabled:opacity-40"
                >
                  Usar
                </button>
              </div>
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
