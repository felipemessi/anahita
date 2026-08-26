"use client";

import { createContext, useCallback, useContext, useState } from "react";

import { formatModifier, rollCheck, type DiceRollResult } from "@/lib/utils/dice";

const MAX_ENTRIES = 5;

interface RollLogEntry extends DiceRollResult {
  id: string;
}

interface RollLogContextValue {
  roll: (label: string, modifier: number) => void;
  entries: RollLogEntry[];
}

const RollLogContext = createContext<RollLogContextValue | null>(null);

/**
 * Provides click-to-roll behaviour for the character sheet: keeps the last
 * few rolls in context so any descendant can trigger a roll, while the
 * visible log itself is rendered where the caller places `<RollLogPanel />`
 * (Fase 8 — moved to the sheet footer so it doesn't compete with content).
 */
export function RollLogProvider({ children }: { children: React.ReactNode }) {
  const [entries, setEntries] = useState<RollLogEntry[]>([]);

  const roll = useCallback((label: string, modifier: number) => {
    const result = rollCheck(label, modifier);
    setEntries((prev) => [{ ...result, id: crypto.randomUUID() }, ...prev].slice(0, MAX_ENTRIES));
  }, []);

  return <RollLogContext.Provider value={{ roll, entries }}>{children}</RollLogContext.Provider>;
}

/** Returns a `roll(label, modifier)` function; must be used inside `RollLogProvider`. */
export function useRoll(): (label: string, modifier: number) => void {
  const context = useContext(RollLogContext);
  if (!context) {
    throw new Error("useRoll must be used within a RollLogProvider");
  }
  return context.roll;
}

/** Renders the recent-rolls log; place inside `RollLogProvider`, wherever it should appear. */
export function RollLogPanel() {
  const context = useContext(RollLogContext);
  if (!context) {
    throw new Error("RollLogPanel must be used within a RollLogProvider");
  }
  const { entries } = context;
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
