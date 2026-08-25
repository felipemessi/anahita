"use client";

import { useCombat } from "@/hooks/use-combat";

/**
 * The last few resolved actions (hit/miss, damage, condition imposed),
 * appearing in real time as `action_resolved` events arrive over the combat
 * WebSocket — every connected client sees the same log, not just whoever
 * declared the action (backlog Fase 6 frontend, história 5).
 */
export function ActionLog() {
  const { actionLog } = useCombat();

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
    </section>
  );
}
