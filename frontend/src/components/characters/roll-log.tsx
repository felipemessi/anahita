"use client";

import { createContext, useCallback, useContext, useState } from "react";

import { DiceRollModal, type DiceRollRequest } from "@/components/characters/dice-roll-modal";
import {
  formatModifier,
  rollCheck,
  rollDiceExpression,
  type DiceRollResult,
} from "@/lib/utils/dice";

const MAX_ENTRIES = 5;

interface RollLogEntry extends DiceRollResult {
  id: string;
}

interface RollLogContextValue {
  /** Client-side 1d20 + modifier roll (ability checks, saves, skills, initiative). */
  roll: (label: string, modifier: number) => void;
  /** A roll already resolved server-side (death saves, hit dice) — still gets the animation. */
  showServerRoll: (request: DiceRollRequest) => void;
  /**
   * A damage roll: sums `diceExpression` (e.g. `"1d8"`) and adds `bonus` —
   * the weapon/spell "Dano" button, always triggered by hand, on its own,
   * never chained after an attack/save roll (the player decides whether
   * the attack actually hit before rolling damage).
   */
  rollDamage: (label: string, diceExpression: string, bonus: number) => void;
  entries: RollLogEntry[];
}

const RollLogContext = createContext<RollLogContextValue | null>(null);

/**
 * Provides click-to-roll behaviour for the character sheet: keeps the last
 * few rolls in context so any descendant can trigger a roll, while the
 * visible log itself is rendered where the caller places `<RollLogPanel />`
 * (Fase 8 — moved to the sheet footer so it doesn't compete with content).
 *
 * Every roll — client-side or already resolved server-side — is first shown
 * through `<DiceRollModal />` (~1s animation, Fase 8) before landing in
 * the log, so the reveal always feels the same regardless of where the
 * actual roll happened.
 */
export function RollLogProvider({ children }: { children: React.ReactNode }) {
  const [entries, setEntries] = useState<RollLogEntry[]>([]);
  // A queue rather than a single slot, so two rolls fired in quick
  // succession never fight over the same modal — the next one starts once
  // the current animation finishes.
  const [queue, setQueue] = useState<DiceRollRequest[]>([]);
  const pending = queue[0] ?? null;

  const enqueue = useCallback((requests: DiceRollRequest[]) => {
    setQueue((current) => [...current, ...requests]);
  }, []);

  const roll = useCallback(
    (label: string, modifier: number) => {
      const result = rollCheck(label, modifier);
      enqueue([{ label, rollResult: result.die, modifier, total: result.total }]);
    },
    [enqueue],
  );

  const showServerRoll = useCallback(
    (request: DiceRollRequest) => {
      enqueue([request]);
    },
    [enqueue],
  );

  const rollDamage = useCallback(
    (label: string, diceExpression: string, bonus: number) => {
      const damageRoll = rollDiceExpression(diceExpression);
      enqueue([{ label, rollResult: damageRoll, modifier: bonus, total: damageRoll + bonus }]);
    },
    [enqueue],
  );

  const handleAnimationComplete = useCallback(() => {
    setQueue((current) => {
      const [done, ...rest] = current;
      if (done) {
        setEntries((prev) =>
          [
            {
              id: crypto.randomUUID(),
              label: done.label,
              die: done.rollResult,
              modifier: done.modifier,
              total: done.total,
            },
            ...prev,
          ].slice(0, MAX_ENTRIES),
        );
      }
      return rest;
    });
  }, []);

  return (
    <RollLogContext.Provider value={{ roll, showServerRoll, rollDamage, entries }}>
      {children}
      <DiceRollModal request={pending} onComplete={handleAnimationComplete} />
    </RollLogContext.Provider>
  );
}

function useRollLogContext(): RollLogContextValue {
  const context = useContext(RollLogContext);
  if (!context) {
    throw new Error("must be used within a RollLogProvider");
  }
  return context;
}

/** Returns a `roll(label, modifier)` function; must be used inside `RollLogProvider`. */
export function useRoll(): (label: string, modifier: number) => void {
  return useRollLogContext().roll;
}

/**
 * Returns a `showServerRoll(request)` function for a roll already resolved
 * server-side (death saves, hit dice) — plays the same animation as a
 * client-side roll before it lands in the log.
 */
export function useShowServerRoll(): (request: DiceRollRequest) => void {
  return useRollLogContext().showServerRoll;
}

/**
 * Returns a `rollDamage(label, diceExpression, bonus)` function for a
 * damage roll (e.g. `rollDamage("Longsword (dano)", "1d8", 2)`) — always
 * fired by hand, on its own, never automatically after an attack/save.
 */
export function useRollDamage(): (
  label: string,
  diceExpression: string,
  bonus: number,
) => void {
  return useRollLogContext().rollDamage;
}

/** Renders the recent-rolls log; place inside `RollLogProvider`, wherever it should appear. */
export function RollLogPanel() {
  const { entries } = useRollLogContext();
  if (entries.length === 0) return null;

  return (
    <section
      aria-label="Rolagens recentes"
      aria-live="polite"
      className="rounded-lg border border-border bg-card p-3"
    >
      <h2 className="text-xs font-semibold uppercase text-muted-foreground">
        Rolagens recentes
      </h2>
      <ul className="mt-2 space-y-1 text-sm">
        {entries.map((entry) => (
          <li key={entry.id} className="flex items-center justify-between font-mono">
            <span className="text-muted-foreground">{entry.label}</span>
            <span>
              {entry.die} {formatModifier(entry.modifier)} ={" "}
              <span className="font-bold">{entry.total}</span>
            </span>
          </li>
        ))}
      </ul>
    </section>
  );
}
