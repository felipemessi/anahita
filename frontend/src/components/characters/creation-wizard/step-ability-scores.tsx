"use client";

import {
  ABILITY_LABELS,
  ABILITY_ORDER,
  STANDARD_ARRAY,
  type WizardState,
} from "@/components/characters/creation-wizard/wizard-state";
import { calculateModifier } from "@/lib/utils/dnd-rules";

/** Assigns the PHB standard array (15/14/13/12/10/8) across the 6 abilities. */
export function StepAbilityScores({
  value,
  onChange,
}: {
  value: WizardState;
  onChange: (patch: Partial<WizardState>) => void;
}) {
  const assigned = Object.values(value.abilityScores).filter(
    (score): score is number => score !== null,
  );

  function setScore(ability: (typeof ABILITY_ORDER)[number], score: number | null) {
    onChange({
      abilityScores: { ...value.abilityScores, [ability]: score },
    });
  }

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">Atributos (array padrão)</h2>
      <p className="text-sm text-muted-foreground">
        Distribua os valores {STANDARD_ARRAY.join(", ")} entre os 6 atributos.
      </p>

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
        {ABILITY_ORDER.map((ability) => {
          const current = value.abilityScores[ability];
          const availableValues = STANDARD_ARRAY.filter(
            (v) => !assigned.includes(v) || v === current,
          );

          return (
            <div key={ability} className="space-y-1">
              <label htmlFor={`ability-${ability}`} className="block text-sm font-medium">
                {ABILITY_LABELS[ability]}
              </label>
              <select
                id={`ability-${ability}`}
                value={current ?? ""}
                onChange={(e) =>
                  setScore(ability, e.target.value ? Number(e.target.value) : null)
                }
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                <option value="">—</option>
                {availableValues.map((v) => (
                  <option key={v} value={v}>
                    {v}
                  </option>
                ))}
              </select>
              {current !== null ? (
                <p className="font-mono text-xs text-muted-foreground">
                  mod {calculateModifier(current) >= 0 ? "+" : ""}
                  {calculateModifier(current)}
                </p>
              ) : null}
            </div>
          );
        })}
      </div>
    </div>
  );
}
