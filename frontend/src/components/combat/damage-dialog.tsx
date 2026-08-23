"use client";

import { useState } from "react";

import { useCombat } from "@/hooks/use-combat";
import type { EncounterParticipant } from "@/types/combat";

const PRESETS = [1, 5, 10];

/**
 * Quick damage/heal control: a preset applies in a single tap; the custom
 * amount takes two (type the amount, tap dano/cura) — always under the
 * "menos de 3 taps" budget from the backlog. Clamps at 0 (can't go negative).
 */
export function DamageDialog({ participant }: { participant: EncounterParticipant }) {
  const { updateParticipant } = useCombat();
  const [amount, setAmount] = useState("");

  function applyDelta(delta: number) {
    const next = Math.max(0, participant.hit_point_current + delta);
    updateParticipant(participant.id, { hitPointCurrent: next });
  }

  function applyCustom(sign: 1 | -1) {
    const parsed = Number(amount);
    if (!Number.isFinite(parsed) || parsed <= 0) return;
    applyDelta(sign * parsed);
    setAmount("");
  }

  return (
    <div className="flex flex-wrap items-center gap-2">
      <div className="flex gap-1">
        {PRESETS.map((preset) => (
          <button
            key={`dmg-${preset}`}
            type="button"
            onClick={() => applyDelta(-preset)}
            className="rounded-md border border-destructive/40 px-2 py-1 text-xs text-destructive hover:bg-destructive/10"
          >
            -{preset}
          </button>
        ))}
        {PRESETS.map((preset) => (
          <button
            key={`heal-${preset}`}
            type="button"
            onClick={() => applyDelta(preset)}
            className="rounded-md border border-emerald-500/40 px-2 py-1 text-xs text-emerald-600 hover:bg-emerald-500/10"
          >
            +{preset}
          </button>
        ))}
      </div>
      <div className="flex items-center gap-1">
        <input
          type="number"
          min={0}
          value={amount}
          onChange={(event) => setAmount(event.target.value)}
          placeholder="Outro"
          aria-label={`Quantidade de dano ou cura para ${participant.name}`}
          className="w-16 rounded-md border border-border bg-background px-2 py-1 text-xs"
        />
        <button
          type="button"
          onClick={() => applyCustom(-1)}
          className="rounded-md border border-destructive/40 px-2 py-1 text-xs text-destructive"
        >
          Dano
        </button>
        <button
          type="button"
          onClick={() => applyCustom(1)}
          className="rounded-md border border-emerald-500/40 px-2 py-1 text-xs text-emerald-600"
        >
          Cura
        </button>
      </div>
    </div>
  );
}
