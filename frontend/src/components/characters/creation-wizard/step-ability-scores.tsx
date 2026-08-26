"use client";

import { useState } from "react";

import { DiceRollModal, type DiceRollRequest } from "@/components/characters/dice-roll-modal";
import {
  ABILITY_LABELS,
  ABILITY_ORDER,
  POINT_BUY_BUDGET,
  POINT_BUY_COSTS,
  POINT_BUY_MAX,
  POINT_BUY_MIN,
  STANDARD_ARRAY,
  type WizardState,
} from "@/components/characters/creation-wizard/wizard-state";
import { roll4d6DropLowest } from "@/lib/utils/dice";
import { calculateModifier } from "@/lib/utils/dnd-rules";
import type { AbilityGenerationMethod } from "@/types/character";

const EMPTY_SCORES: WizardState["abilityScores"] = {
  str: null,
  dex: null,
  con: null,
  int: null,
  wis: null,
  cha: null,
};

const METHODS: { value: AbilityGenerationMethod; label: string }[] = [
  { value: "standard_array", label: "Array padrão" },
  { value: "point_buy", label: "Compra de pontos" },
  { value: "roll", label: "Rolagem" },
  { value: "custom", label: "Livre" },
];

/**
 * Ability score generation method picker (Fase 8): standard array and roll
 * both work as "assign a fixed pool of 6 values to the 6 abilities"; point
 * buy tracks a 27-point budget per the PHB cost table; custom is free
 * typing. The chosen method is sent as `generation_method` so the backend
 * validates standard array/point buy the same way (see `domain.py`).
 */
export function StepAbilityScores({
  value,
  onChange,
}: {
  value: WizardState;
  onChange: (patch: Partial<WizardState>) => void;
}) {
  const [rollPool, setRollPool] = useState<number[]>([]);
  const [pendingPool, setPendingPool] = useState<number[] | null>(null);
  const [pendingRoll, setPendingRoll] = useState<DiceRollRequest | null>(null);

  function setMethod(method: AbilityGenerationMethod) {
    onChange({ abilityGenerationMethod: method, abilityScores: { ...EMPTY_SCORES } });
    setRollPool([]);
  }

  function setScore(ability: (typeof ABILITY_ORDER)[number], score: number | null) {
    onChange({
      abilityScores: { ...value.abilityScores, [ability]: score },
    });
  }

  function handleGenerateRolls() {
    const rolls = Array.from({ length: 6 }, () => roll4d6DropLowest());
    setPendingPool(rolls);
    setPendingRoll({
      label: "Atributos",
      rollResult: rolls[0] ?? 0,
      modifier: 0,
      total: rolls.reduce((sum, r) => sum + r, 0),
    });
  }

  function handleRollAnimationComplete() {
    if (pendingPool) {
      setRollPool(pendingPool);
      onChange({ abilityScores: { ...EMPTY_SCORES } });
    }
    setPendingPool(null);
    setPendingRoll(null);
  }

  function pointBuyScore(ability: (typeof ABILITY_ORDER)[number]): number {
    return value.abilityScores[ability] ?? POINT_BUY_MIN;
  }

  function pointBuySpent(): number {
    return ABILITY_ORDER.reduce(
      (sum, ability) => sum + (POINT_BUY_COSTS[pointBuyScore(ability)] ?? 0),
      0,
    );
  }

  function adjustPointBuy(ability: (typeof ABILITY_ORDER)[number], delta: 1 | -1) {
    const current = pointBuyScore(ability);
    const next = current + delta;
    if (next < POINT_BUY_MIN || next > POINT_BUY_MAX) return;
    const deltaCost = (POINT_BUY_COSTS[next] ?? 0) - (POINT_BUY_COSTS[current] ?? 0);
    if (pointBuySpent() + deltaCost > POINT_BUY_BUDGET) return;
    setScore(ability, next);
  }

  const method = value.abilityGenerationMethod;
  const pool = method === "roll" ? rollPool : STANDARD_ARRAY;

  /**
   * Values from `pool` still free for `ability` to pick — accounts for
   * duplicates (the "roll" pool can repeat a value across two abilities,
   * unlike the standard array) by only excluding as many copies of a value
   * as are actually assigned to *other* abilities.
   */
  function availableForAbility(ability: (typeof ABILITY_ORDER)[number]): number[] {
    const usedElsewhere = new Map<number, number>();
    for (const other of ABILITY_ORDER) {
      if (other === ability) continue;
      const used = value.abilityScores[other];
      if (used !== null) usedElsewhere.set(used, (usedElsewhere.get(used) ?? 0) + 1);
    }
    const poolCounts = new Map<number, number>();
    for (const v of pool) poolCounts.set(v, (poolCounts.get(v) ?? 0) + 1);

    const result: number[] = [];
    for (const [v, count] of poolCounts) {
      const remaining = count - (usedElsewhere.get(v) ?? 0);
      for (let i = 0; i < remaining; i++) result.push(v);
    }
    return result.sort((a, b) => b - a);
  }

  const spent = pointBuySpent();

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">Atributos</h2>

      <div className="flex flex-wrap gap-2" role="radiogroup" aria-label="Método de geração">
        {METHODS.map((m) => (
          <button
            key={m.value}
            type="button"
            role="radio"
            aria-checked={method === m.value}
            onClick={() => setMethod(m.value)}
            className={`rounded-md border px-3 py-1.5 text-sm ${
              method === m.value
                ? "border-primary bg-primary/10 text-primary"
                : "border-border hover:bg-secondary"
            }`}
          >
            {m.label}
          </button>
        ))}
      </div>

      {method === "standard_array" || method === "roll" ? (
        <>
          <p className="text-sm text-muted-foreground">
            {method === "standard_array"
              ? `Distribua os valores ${STANDARD_ARRAY.join(", ")} entre os 6 atributos.`
              : "Role 4d6 (descarta o menor) para gerar 6 valores e distribua entre os atributos."}
          </p>
          {method === "roll" ? (
            <button
              type="button"
              onClick={handleGenerateRolls}
              className="rounded-md border border-border px-3 py-1.5 text-sm hover:bg-secondary"
            >
              {rollPool.length > 0 ? "Rolar novamente" : "Rolar atributos"}
            </button>
          ) : null}

          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
            {ABILITY_ORDER.map((ability) => {
              const current = value.abilityScores[ability];
              const availableValues = availableForAbility(ability);

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
                    disabled={method === "roll" && pool.length === 0}
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm disabled:opacity-40"
                  >
                    <option value="">—</option>
                    {availableValues.map((v, i) => (
                      <option key={`${v}-${i}`} value={v}>
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
        </>
      ) : null}

      {method === "point_buy" ? (
        <>
          <p className="text-sm text-muted-foreground">
            Orçamento de {POINT_BUY_BUDGET} pontos (8 a 15 por atributo).{" "}
            <span className={spent > POINT_BUY_BUDGET ? "text-destructive" : ""}>
              {spent}/{POINT_BUY_BUDGET} gastos
            </span>
          </p>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
            {ABILITY_ORDER.map((ability) => {
              const current = pointBuyScore(ability);
              return (
                <div key={ability} className="space-y-1">
                  <p className="block text-sm font-medium">{ABILITY_LABELS[ability]}</p>
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      aria-label={`Diminuir ${ABILITY_LABELS[ability]}`}
                      onClick={() => adjustPointBuy(ability, -1)}
                      disabled={current <= POINT_BUY_MIN}
                      className="rounded-md border border-border px-2 py-1 text-sm disabled:opacity-40"
                    >
                      −
                    </button>
                    <span className="w-6 text-center font-mono">{current}</span>
                    <button
                      type="button"
                      aria-label={`Aumentar ${ABILITY_LABELS[ability]}`}
                      onClick={() => adjustPointBuy(ability, 1)}
                      disabled={
                        current >= POINT_BUY_MAX ||
                        spent +
                          ((POINT_BUY_COSTS[current + 1] ?? 0) - (POINT_BUY_COSTS[current] ?? 0)) >
                          POINT_BUY_BUDGET
                      }
                      className="rounded-md border border-border px-2 py-1 text-sm disabled:opacity-40"
                    >
                      +
                    </button>
                  </div>
                  <p className="font-mono text-xs text-muted-foreground">
                    mod {calculateModifier(current) >= 0 ? "+" : ""}
                    {calculateModifier(current)}
                  </p>
                </div>
              );
            })}
          </div>
        </>
      ) : null}

      {method === "custom" ? (
        <>
          <p className="text-sm text-muted-foreground">Digite os valores livremente.</p>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
            {ABILITY_ORDER.map((ability) => {
              const current = value.abilityScores[ability];
              return (
                <div key={ability} className="space-y-1">
                  <label htmlFor={`ability-${ability}`} className="block text-sm font-medium">
                    {ABILITY_LABELS[ability]}
                  </label>
                  <input
                    id={`ability-${ability}`}
                    type="number"
                    value={current ?? ""}
                    onChange={(e) =>
                      setScore(ability, e.target.value ? Number(e.target.value) : null)
                    }
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  />
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
        </>
      ) : null}

      <DiceRollModal request={pendingRoll} onComplete={handleRollAnimationComplete} />
    </div>
  );
}
