"use client";

import { useCombat } from "@/hooks/use-combat";

/** Fixed footer button that advances the current turn (DM only). */
export function TurnIndicator() {
  const { encounter, advanceTurn } = useCombat();

  if (!encounter || encounter.status !== "active") return null;

  return (
    <button
      type="button"
      onClick={advanceTurn}
      className="sticky bottom-4 mt-auto rounded-md bg-primary px-4 py-3 text-sm font-medium text-primary-foreground hover:opacity-90"
    >
      Avançar turno · Round {encounter.current_round}
    </button>
  );
}
