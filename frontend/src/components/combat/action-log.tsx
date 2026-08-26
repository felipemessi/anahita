"use client";

import { useEffect, useRef, useState } from "react";

import { DiceRollModal, type DiceRollRequest } from "@/components/characters/dice-roll-modal";
import { useCombat } from "@/hooks/use-combat";
import type { DeclareActionResult } from "@/lib/ws/types";

/**
 * The last few resolved actions (hit/miss, damage, condition imposed),
 * appearing in real time as `action_resolved` events arrive over the combat
 * WebSocket — every connected client sees the same log, not just whoever
 * declared the action (backlog Fase 6 frontend, história 5).
 *
 * Each new entry with a roll animates first (Fase 8) — this only delays
 * how *this* client reveals its own copy of that one log line; the entry
 * itself, and any participant state a future update might carry, land in
 * `combat-provider.tsx`'s state immediately and identically for everyone,
 * so this never risks the DM/players seeing different combat state.
 */
export function ActionLog() {
  const { actionLog } = useCombat();
  const [pendingRoll, setPendingRoll] = useState<DiceRollRequest | null>(null);
  const queueRef = useRef<DiceRollRequest[]>([]);
  const seenTopRef = useRef<DeclareActionResult | null>(null);

  useEffect(() => {
    const newest = actionLog[0];
    if (!newest || newest === seenTopRef.current) return;
    seenTopRef.current = newest;

    const requests = rollRequestsFor(newest);
    if (requests.length === 0) return;
    queueRef.current = requests.slice(1);
    setPendingRoll(requests[0] ?? null);
  }, [actionLog]);

  function handleRollComplete() {
    setPendingRoll(queueRef.current.shift() ?? null);
  }

  if (actionLog.length === 0) return null;

  return (
    <section aria-label="Log de ações" className="rounded-lg border border-border bg-card p-3">
      <h2 className="text-xs font-semibold uppercase text-muted-foreground">
        Últimas ações
      </h2>
      <ul className="mt-2 space-y-1 text-sm">
        {actionLog.map((result, index) => (
          <li key={index} className="text-muted-foreground">
            {result.description}
          </li>
        ))}
      </ul>
      <DiceRollModal request={pendingRoll} onComplete={handleRollComplete} />
    </section>
  );
}

/** The rolls to animate for one resolved action, in reveal order. */
function rollRequestsFor(result: DeclareActionResult): DiceRollRequest[] {
  const requests: DiceRollRequest[] = [];
  if (result.attack_roll != null) {
    requests.push({
      label: "Ataque",
      rollResult: result.attack_roll,
      modifier: result.attack_bonus ?? 0,
      total: result.attack_roll + (result.attack_bonus ?? 0),
    });
  }
  if (result.attacker_check != null) {
    requests.push({
      label: "Teste do atacante",
      rollResult: result.attacker_check,
      modifier: 0,
      total: result.attacker_check,
    });
  }
  if (result.target_check != null) {
    requests.push({
      label: "Teste do alvo",
      rollResult: result.target_check,
      modifier: 0,
      total: result.target_check,
    });
  }
  if (result.damage_rolled != null) {
    requests.push({
      label: "Dano",
      rollResult: result.damage_rolled,
      modifier: 0,
      total: result.damage_rolled,
    });
  }
  return requests;
}
