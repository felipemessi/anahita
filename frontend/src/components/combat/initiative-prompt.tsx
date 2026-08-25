"use client";

import { useState } from "react";

import { useCombat } from "@/hooks/use-combat";
import type { EncounterParticipant } from "@/types/combat";

/**
 * Blocks turn advancement until every active participant has rolled
 * initiative — shown once the encounter is active and any participant is
 * still missing one. Any campaign member may roll for their own
 * participant; the DM may roll for any (server-enforced, see
 * `useCombat().rollInitiative`). The button always rolls automatically
 * (server-side `1d20 + DEX`) — "digitar manualmente" is an alternative,
 * never the default (backlog Fase 6 frontend, história 7).
 */
export function InitiativePrompt() {
  const { encounter, rollInitiative } = useCombat();
  const [manualForId, setManualForId] = useState<string | null>(null);
  const [manualValue, setManualValue] = useState("");

  if (!encounter || encounter.status !== "active") return null;
  const missing = encounter.participants.filter(
    (p) => p.is_active && p.initiative === null,
  );
  if (missing.length === 0) return null;

  function handleManualConfirm(participant: EncounterParticipant) {
    if (manualValue === "") return;
    rollInitiative(participant.id, Number(manualValue));
    setManualForId(null);
    setManualValue("");
  }

  return (
    <section
      aria-label="Rolagem de iniciativa"
      className="rounded-lg border border-border bg-card p-4"
    >
      <h2 className="font-semibold">Rolagem de iniciativa</h2>
      <p className="mt-1 text-sm text-muted-foreground">
        O combate só avança quando todos os participantes rolarem iniciativa.
      </p>
      <ul className="mt-2 space-y-1">
        {missing.map((participant) => (
          <li key={participant.id} className="space-y-1 text-sm">
            <div className="flex items-center justify-between">
              <span>{participant.name}</span>
              <div className="flex items-center gap-2 text-xs">
                <button
                  type="button"
                  onClick={() => rollInitiative(participant.id)}
                  className="rounded-md border border-border px-3 py-1 hover:bg-secondary"
                >
                  Rolar iniciativa
                </button>
                <button
                  type="button"
                  onClick={() =>
                    setManualForId(manualForId === participant.id ? null : participant.id)
                  }
                  className="text-muted-foreground underline"
                >
                  digitar manualmente
                </button>
              </div>
            </div>
            {manualForId === participant.id ? (
              <div className="flex items-center gap-2">
                <input
                  type="number"
                  value={manualValue}
                  onChange={(e) => setManualValue(e.target.value)}
                  aria-label={`Iniciativa manual de ${participant.name}`}
                  className="w-16 rounded-md border border-input bg-background px-2 py-1 text-xs"
                />
                <button
                  type="button"
                  onClick={() => handleManualConfirm(participant)}
                  className="rounded-md border border-border px-2 py-1 text-xs hover:bg-secondary"
                >
                  Confirmar
                </button>
              </div>
            ) : null}
          </li>
        ))}
      </ul>
    </section>
  );
}
