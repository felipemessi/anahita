"use client";

import { useRef, useState } from "react";

import { useRollDeathSave } from "@/hooks/use-character";
import { ApiError } from "@/lib/api/client";

/**
 * Appears when `hit_point_current === 0`: three success/failure markers
 * plus a "rolar" button — stable (3 successes) and dead (3 failures) each
 * get a clear visual state. Healing above 0 HP resets the track
 * server-side, so the component simply disappears once that happens.
 *
 * The backend doesn't persist a separate "stabilized" flag — 3 successes
 * just resets both counters to 0, same shape as "hasn't rolled yet" — so
 * stabilized is inferred client-side from having *had* progress (a prior
 * render with successes/failures > 0) that then reset to 0/0 without
 * dying; this only holds for the component's current mount (a page
 * reload loses it, falling back to the plain not-yet-rolled view).
 */
export function DeathSaveTracker({
  characterId,
  hitPointCurrent,
  successes,
  failures,
  isDead,
}: {
  characterId: string;
  hitPointCurrent: number;
  successes: number;
  failures: number;
  isDead: boolean;
}) {
  const rollDeathSave = useRollDeathSave(characterId);
  const [error, setError] = useState<string | null>(null);
  const hadProgress = useRef(false);
  if (successes > 0 || failures > 0) {
    hadProgress.current = true;
  } else if (hitPointCurrent !== 0) {
    hadProgress.current = false;
  }
  const stabilized = !isDead && successes === 0 && failures === 0 && hadProgress.current;

  if (hitPointCurrent !== 0) return null;

  async function handleRoll() {
    setError(null);
    try {
      await rollDeathSave.mutateAsync({});
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Não foi possível rolar o teste de morte.");
    }
  }

  return (
    <section
      aria-label="Testes de morte"
      className="rounded-lg border border-destructive/50 bg-card p-4"
    >
      <h2 className="font-semibold">Testes de morte</h2>

      {isDead ? (
        <p className="mt-2 font-semibold text-destructive">Morto</p>
      ) : stabilized ? (
        <p className="mt-2 font-semibold text-emerald-500">Estável</p>
      ) : (
        <>
          <div className="mt-2 flex items-center gap-6 text-sm">
            <MarkerRow label="Sucessos" count={successes} colorClass="bg-emerald-500" />
            <MarkerRow label="Falhas" count={failures} colorClass="bg-destructive" />
          </div>
          <button
            type="button"
            onClick={handleRoll}
            disabled={rollDeathSave.isPending}
            className="mt-3 rounded-md border border-border px-3 py-1.5 text-sm hover:bg-secondary disabled:opacity-40"
          >
            Rolar
          </button>
        </>
      )}
      {error ? (
        <p role="alert" className="mt-2 text-sm text-destructive">
          {error}
        </p>
      ) : null}
    </section>
  );
}

function MarkerRow({
  label,
  count,
  colorClass,
}: {
  label: string;
  count: number;
  colorClass: string;
}) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-xs text-muted-foreground">{label}</span>
      <div className="flex gap-1" aria-label={`${count} de 3 ${label.toLowerCase()}`}>
        {Array.from({ length: 3 }, (_, i) => (
          <span
            key={i}
            className={`h-3 w-3 rounded-full border border-border ${
              i < count ? colorClass : "bg-transparent"
            }`}
          />
        ))}
      </div>
    </div>
  );
}
