"use client";

import { useState } from "react";

import type { useCombat } from "@/hooks/use-combat";
import { useResourceOptions, useSpendCharacterResource } from "@/hooks/use-character";
import { ApiError } from "@/lib/api/client";
import type { CharacterResource } from "@/types/character";
import type { EncounterParticipant } from "@/types/combat";

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
 * Resource option `Feature.index` values that trigger a real mechanical
 * effect instead of pure bookkeeping — mirrors backend
 * `CombatService._CLASS_RESOURCE_EFFECTS` (Fase 12). Only meaningful when
 * `combat` is supplied (this row is rendered inside a live encounter, via
 * `ActionPicker`) — outside combat, every option is bookkeeping-only,
 * same as before this fase.
 */
const RESOURCE_EFFECT_OPTION_INDEXES = new Set(["channel-divinity-turn-undead"]);

/** Context supplied only when `ClassResources` is rendered inside `ActionPicker` (a live encounter). */
export interface ClassResourcesCombatContext {
  participantId: string;
  otherParticipants: EncounterParticipant[];
  declareAction: ReturnType<typeof useCombat>["declareAction"];
}

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
 *
 * When `combat` is supplied and the chosen option has a mapped mechanical
 * effect (Channel Divinity: Turn Undead, so far — Fase 12), "usar" is
 * replaced by a target picker; declaring sends `use_class_resource` over
 * the combat WebSocket instead of spending the resource directly, so the
 * server resolves the saving throw(s) and applies the effect in the same
 * call. Every other case (no combat context, or an option with no mapped
 * effect) keeps the old direct-spend behavior unchanged.
 */
export function ClassResources({
  characterId,
  resources,
  combat,
}: {
  characterId: string;
  resources: CharacterResource[];
  combat?: ClassResourcesCombatContext;
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
            combat={combat}
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
  combat,
}: {
  characterId: string;
  resource: CharacterResource;
  selectedOptionId: string;
  onSelectOption: (optionId: string) => void;
  onUse: (resourceKey: string, optionId?: string) => void;
  isPending: boolean;
  combat?: ClassResourcesCombatContext;
}) {
  const { data: options } = useResourceOptions(characterId, resource.resource_key);
  const available = resource.max - resource.used;
  const requiresChoice = (options?.length ?? 0) > 1;
  const [targetIds, setTargetIds] = useState<string[]>([]);

  const selectedOptionIndex = options?.find((o) => o.id === selectedOptionId)?.index ?? null;
  const hasMappedEffect =
    combat != null &&
    selectedOptionIndex != null &&
    RESOURCE_EFFECT_OPTION_INDEXES.has(selectedOptionIndex) &&
    // A resource with no options at all (or a single unnamed one) never
    // reaches here with a `selectedOptionId` — nothing to check against.
    (requiresChoice ? selectedOptionId !== "" : true);

  const canUse = hasMappedEffect
    ? available > 0 && !isPending && targetIds.length > 0
    : available > 0 && !isPending && (!requiresChoice || selectedOptionId !== "");

  function toggleTarget(participantId: string) {
    setTargetIds((prev) =>
      prev.includes(participantId)
        ? prev.filter((id) => id !== participantId)
        : [...prev, participantId],
    );
  }

  function handleUseClick() {
    if (hasMappedEffect && combat) {
      const [target_id, ...additional_target_ids] = targetIds;
      if (!target_id) return;
      combat.declareAction({
        actionType: "use_class_resource",
        participant_id: combat.participantId,
        target_id,
        additional_target_ids,
        resource_key: resource.resource_key,
        resource_option_id: selectedOptionId || undefined,
      });
      setTargetIds([]);
      onSelectOption("");
      return;
    }
    onUse(resource.resource_key, requiresChoice ? selectedOptionId : undefined);
  }

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
            onChange={(e) => {
              onSelectOption(e.target.value);
              setTargetIds([]);
            }}
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
          onClick={handleUseClick}
          disabled={!canUse}
          className="rounded-md border border-border px-3 py-1 text-xs hover:bg-secondary disabled:opacity-40"
        >
          Usar
        </button>
      </div>
      {hasMappedEffect && combat ? (
        <fieldset className="w-full rounded-md border border-dashed border-border p-2 text-xs">
          <legend className="px-1 text-muted-foreground">Alvos afetados</legend>
          <div className="flex flex-wrap gap-2">
            {combat.otherParticipants.map((p) => (
              <label key={p.id} className="flex items-center gap-1">
                <input
                  type="checkbox"
                  checked={targetIds.includes(p.id)}
                  onChange={() => toggleTarget(p.id)}
                />
                {p.name}
              </label>
            ))}
          </div>
        </fieldset>
      ) : null}
    </li>
  );
}
