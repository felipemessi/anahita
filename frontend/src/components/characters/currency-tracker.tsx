"use client";

import { useState, type FormEvent } from "react";

import { useUpdateCharacterCurrency } from "@/hooks/use-character";
import { ApiError } from "@/lib/api/client";

/**
 * 1 cp / 10 sp / 100 gp / 1000 pp — mirrors the backend's copper
 * normalization. `ep` (electrum) is intentionally left out, per the
 * group's decision (Fase 8) — `Character.currency_cp` still stores a
 * single normalized copper total either way.
 */
const DENOMINATIONS = [
  { key: "pp", label: "PP", rate: 1000 },
  { key: "gp", label: "GP", rate: 100 },
  { key: "sp", label: "SP", rate: 10 },
  { key: "cp", label: "CP", rate: 1 },
] as const;

type DenominationKey = (typeof DENOMINATIONS)[number]["key"];

const EMPTY_AMOUNTS: Record<DenominationKey, string> = { pp: "", gp: "", sp: "", cp: "" };

/** Splits a copper total into the largest denominations first, for display only. */
function splitCopper(totalCp: number): string {
  let remaining = totalCp;
  const parts: string[] = [];
  for (const { label, rate } of DENOMINATIONS) {
    const count = Math.floor(remaining / rate);
    if (count > 0) {
      parts.push(`${count} ${label}`);
      remaining -= count * rate;
    }
  }
  return parts.length > 0 ? parts.join(" ") : "0 CP";
}

/**
 * Current balance (split into denominations for display) plus a per-
 * denomination gain/spend form — one input per cp/sp/gp/pp, each accepting
 * a positive (gain) or negative (spend) count, all applied together as a
 * single copper delta (Fase 8: e.g. "+2 gp -5 sp" in one submission). An
 * optimistic update reverts if the spend would leave a negative balance
 * (backend 422).
 */
export function CurrencyTracker({
  characterId,
  currencyCp,
}: {
  characterId: string;
  currencyCp: number;
}) {
  const updateCurrency = useUpdateCharacterCurrency(characterId);
  const [amounts, setAmounts] = useState<Record<DenominationKey, string>>(EMPTY_AMOUNTS);
  const [error, setError] = useState<string | null>(null);

  function totalDeltaCp(): number {
    return DENOMINATIONS.reduce(
      (sum, { key, rate }) => sum + (Number(amounts[key]) || 0) * rate,
      0,
    );
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const delta = totalDeltaCp();
    if (delta === 0) return;
    setError(null);
    try {
      await updateCurrency.mutateAsync({ delta });
      setAmounts(EMPTY_AMOUNTS);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Não foi possível registrar a moeda.");
    }
  }

  const delta = totalDeltaCp();

  return (
    <section aria-label="Moeda" className="rounded-lg border border-border bg-card p-4">
      <h2 className="font-semibold">Moeda</h2>
      <p className="mt-1 font-mono text-lg">{splitCopper(currencyCp)}</p>

      <form onSubmit={handleSubmit} className="mt-3 space-y-2">
        <div className="flex flex-wrap items-end gap-3">
          {DENOMINATIONS.map(({ key, label }) => (
            <div key={key} className="space-y-1">
              <label htmlFor={`currency-${key}`} className="text-xs text-muted-foreground">
                {label}
              </label>
              <input
                id={`currency-${key}`}
                type="number"
                value={amounts[key]}
                onChange={(e) => setAmounts((prev) => ({ ...prev, [key]: e.target.value }))}
                placeholder="0"
                className="w-16 rounded-md border border-input bg-background px-2 py-1.5 text-sm"
              />
            </div>
          ))}
          <button
            type="submit"
            disabled={delta === 0 || updateCurrency.isPending}
            className="rounded-md border border-border px-3 py-1.5 text-sm hover:bg-secondary disabled:opacity-40"
          >
            Registrar
          </button>
        </div>
        <p className="text-xs text-muted-foreground">
          Valores negativos são gastos. Delta total: {delta >= 0 ? "+" : ""}
          {delta} cp.
        </p>
      </form>
      {error ? (
        <p role="alert" className="mt-1 text-sm text-destructive">
          {error}
        </p>
      ) : null}
    </section>
  );
}
