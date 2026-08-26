"use client";

import { useEffect, useState } from "react";

import { formatModifier } from "@/lib/utils/dice";

/** ~1.5s of random values before locking to the real result (Fase 8). */
const SPIN_MS = 1500;
const SPIN_TICK_MS = 80;
/** How long the locked result stays visible before auto-closing. */
const HOLD_MS = 900;

export interface DiceRollRequest {
  /** What was rolled, e.g. "Força" or "Dado de vida (Fighter)". */
  label: string;
  /** The real die result (sum of all dice, before the modifier). */
  rollResult: number;
  /** The modifier/bonus added to `rollResult`. */
  modifier: number;
  /** `rollResult + modifier`. */
  total: number;
}

/**
 * Overlay shown before revealing a roll's result, everywhere a roll happens
 * (ability/save/skill/initiative via `roll-log.tsx`, death saves, hit dice —
 * backlog Fase 8). Purely presentational: the roll itself already happened
 * (client-side or server-side) by the time `request` is set — this only
 * delays and dresses up how the number is revealed.
 */
export function DiceRollModal({
  request,
  onComplete,
}: {
  request: DiceRollRequest | null;
  onComplete: () => void;
}) {
  const [displayValue, setDisplayValue] = useState<number | null>(null);
  const [settled, setSettled] = useState(false);

  useEffect(() => {
    if (!request) {
      setDisplayValue(null);
      setSettled(false);
      return;
    }

    setSettled(false);
    const spinRange = Math.max(request.rollResult, 20);
    const tick = setInterval(() => {
      setDisplayValue(1 + Math.floor(Math.random() * spinRange));
    }, SPIN_TICK_MS);

    const settle = setTimeout(() => {
      clearInterval(tick);
      setDisplayValue(request.rollResult);
      setSettled(true);
    }, SPIN_MS);

    const close = setTimeout(() => {
      onComplete();
    }, SPIN_MS + HOLD_MS);

    return () => {
      clearInterval(tick);
      clearTimeout(settle);
      clearTimeout(close);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- re-run only when a new request comes in
  }, [request]);

  if (!request) return null;

  return (
    <div
      role="dialog"
      aria-label={`Rolando ${request.label}`}
      aria-live="polite"
      className="fixed inset-0 z-50 flex items-center justify-center bg-background/70"
    >
      <div className="rounded-lg border border-border bg-card px-8 py-6 text-center shadow-lg">
        <p className="text-xs uppercase tracking-wide text-muted-foreground">{request.label}</p>
        <p className="mt-2 font-mono text-4xl tabular-nums">{displayValue}</p>
        {settled ? (
          <p className="mt-2 font-mono text-sm text-muted-foreground">
            {request.rollResult} {formatModifier(request.modifier)} ={" "}
            <span className="font-bold text-foreground">{request.total}</span>
          </p>
        ) : null}
      </div>
    </div>
  );
}
