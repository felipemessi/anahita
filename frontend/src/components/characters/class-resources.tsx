"use client";

import { useState } from "react";

import { useResourceOptions, useSpendCharacterResource } from "@/hooks/use-character";
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
 *
 * A resource with more than one named option (e.g. a Paladin/Cleric's
 * Channel Divinity: Sacred Weapon vs. Turn the Unholy) shows a selector
 * before "usar" is enabled — one with none or exactly one option uses
 * directly (Fase 8).
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
  const [selectedOption, setSelectedOption] = useState<Record<string, string>>({});

  if (resources.length === 0) return null;

  async function handleUse(resourceKey: string, optionId?: string) {
    setError(null);
    try {
      await spend.mutateAsync({ resourceKey, optionId });
      setSelectedOption((prev) => ({ ...prev, [resourceKey]: "" }));
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
        {resources.map((resource) => (
          <ResourceRow
            key={resource.resource_key}
            characterId={characterId}
            resource={resource}
            selectedOptionId={selectedOption[resource.resource_key] ?? ""}
            onSelectOption={(optionId) =>
              setSelectedOption((prev) => ({ ...prev, [resource.resource_key]: optionId }))
            }
            onUse={handleUse}
            isPending={spend.isPending}
          />
        ))}
      </ul>
      {error ? (
        <p role="alert" className="mt-2 text-sm text-destructive">
          {error}
        </p>
      ) : null}
    </section>
  );
}

function ResourceRow({
  characterId,
  resource,
  selectedOptionId,
  onSelectOption,
  onUse,
  isPending,
}: {
  characterId: string;
  resource: CharacterResource;
  selectedOptionId: string;
  onSelectOption: (optionId: string) => void;
  onUse: (resourceKey: string, optionId?: string) => void;
  isPending: boolean;
}) {
  const { data: options } = useResourceOptions(characterId, resource.resource_key);
  const available = resource.max - resource.used;
  const requiresChoice = (options?.length ?? 0) > 1;
  const canUse = available > 0 && !isPending && (!requiresChoice || selectedOptionId !== "");

  return (
    <li className="flex flex-wrap items-center justify-between gap-2 text-sm">
      <span>{RESOURCE_LABEL[resource.resource_key] ?? resource.resource_key}</span>
      <div className="flex items-center gap-2">
        <span className="font-mono text-xs text-muted-foreground">
          {available}/{resource.max}
        </span>
        {requiresChoice ? (
          <select
            aria-label={`Opção de ${RESOURCE_LABEL[resource.resource_key] ?? resource.resource_key}`}
            value={selectedOptionId}
            onChange={(e) => onSelectOption(e.target.value)}
            className="rounded-md border border-input bg-background px-2 py-1 text-xs"
          >
            <option value="">Escolha uma opção</option>
            {options?.map((option) => (
              <option key={option.id} value={option.id}>
                {option.feature_name}
              </option>
            ))}
          </select>
        ) : null}
        <button
          type="button"
          onClick={() =>
            onUse(resource.resource_key, requiresChoice ? selectedOptionId : undefined)
          }
          disabled={!canUse}
          className="rounded-md border border-border px-3 py-1 text-xs hover:bg-secondary disabled:opacity-40"
        >
          Usar
        </button>
      </div>
    </li>
  );
}
