"use client";

import { useState, type FormEvent } from "react";

import { useUpdateCharacterCurrency } from "@/hooks/use-character";
import { ApiError } from "@/lib/api/client";

/** 1 cp / 10 sp / 50 ep / 100 gp / 1000 pp — mirrors the backend's copper normalization. */
const DENOMINATIONS = [
  { label: "pp", rate: 1000 },
  { label: "gp", rate: 100 },
  { label: "ep", rate: 50 },
  { label: "sp", rate: 10 },
  { label: "cp", rate: 1 },
] as const;

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
  return parts.length > 0 ? parts.join(" ") : "0 cp";
}

/**
 * Current balance (split into denominations for display) plus a quick
 * gain/spend form — an optimistic update reverts if the spend would leave
 * a negative balance (backend 422).
 */
export function CurrencyTracker({
  characterId,
  currencyCp,
}: {
  characterId: string;
  currencyCp: number;
}) {
  const updateCurrency = useUpdateCharacterCurrency(characterId);
  const [amount, setAmount] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function handleChange(sign: 1 | -1) {
    const value = Number(amount);
    if (!value || value <= 0) return;
    setError(null);
    try {
      await updateCurrency.mutateAsync({ delta: sign * value });
      setAmount("");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Não foi possível registrar a moeda.");
    }
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
  }

  return (
    <section aria-label="Moeda" className="rounded-lg border border-border bg-card p-4">
      <h2 className="font-semibold">Moeda</h2>
      <p className="mt-1 font-mono text-lg">{splitCopper(currencyCp)}</p>

      <form onSubmit={handleSubmit} className="mt-3 flex flex-wrap items-end gap-3">
        <div className="space-y-1">
          <label htmlFor="currency-amount" className="text-xs text-muted-foreground">
            Quantidade (em cp)
          </label>
          <input
            id="currency-amount"
            type="number"
            min={1}
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            className="w-28 rounded-md border border-input bg-background px-2 py-1.5 text-sm"
          />
        </div>
        <button
          type="button"
          onClick={() => handleChange(1)}
          disabled={!amount || updateCurrency.isPending}
          className="rounded-md border border-border px-3 py-1.5 text-sm hover:bg-secondary disabled:opacity-40"
        >
          Ganhar
        </button>
        <button
          type="button"
          onClick={() => handleChange(-1)}
          disabled={!amount || updateCurrency.isPending}
          className="rounded-md border border-border px-3 py-1.5 text-sm hover:bg-secondary disabled:opacity-40"
        >
          Gastar
        </button>
      </form>
      {error ? (
        <p role="alert" className="mt-1 text-sm text-destructive">
          {error}
        </p>
      ) : null}
    </section>
  );
}
