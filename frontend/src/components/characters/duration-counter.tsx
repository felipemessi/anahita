"use client";

import { useEffect, useRef, useState } from "react";

import type { ConcentrationRemaining } from "@/types/character";

/** Rounds/seconds left at which the counter switches to its "about to expire" look. */
const URGENT_ROUNDS_THRESHOLD = 1;
const URGENT_SECONDS_THRESHOLD = 6;

/**
 * Rounds-mode countdown: starts from `remainingRounds` (as computed by the
 * backend at the last character fetch) and decrements client-side as
 * `currentRound` — the combat tracker's WS-driven round number, via
 * `turn_advanced` — advances past the round it was fetched at. Resets its
 * baseline whenever a fresh `remainingRounds` arrives (new fetch, or a
 * different spell).
 */
function useRoundsRemaining(remainingRounds: number, currentRound: number | null): number {
  const baselineRoundRef = useRef<number | null>(currentRound);
  const baseRemainingRef = useRef(remainingRounds);
  const [display, setDisplay] = useState(remainingRounds);

  useEffect(() => {
    baselineRoundRef.current = currentRound;
    baseRemainingRef.current = remainingRounds;
    setDisplay(remainingRounds);
    // Only re-baseline when the server-computed value itself changes —
    // `currentRound` drift is handled by the effect below.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [remainingRounds]);

  useEffect(() => {
    if (currentRound === null || baselineRoundRef.current === null) return;
    const elapsed = currentRound - baselineRoundRef.current;
    if (elapsed > 0) {
      setDisplay(Math.max(0, baseRemainingRef.current - elapsed));
    }
  }, [currentRound]);

  return display;
}

/**
 * Real-time-mode countdown: ticks down from `remainingSeconds` client-side,
 * independent of any WS event, resetting whenever a fresh value arrives.
 */
function useSecondsRemaining(remainingSeconds: number): number {
  const [display, setDisplay] = useState(remainingSeconds);

  useEffect(() => {
    setDisplay(remainingSeconds);
    if (remainingSeconds <= 0) return;

    const deadline = Date.now() + remainingSeconds * 1000;
    const tick = () => {
      setDisplay(Math.max(0, (deadline - Date.now()) / 1000));
    };
    const interval = setInterval(tick, 1000);
    return () => clearInterval(interval);
  }, [remainingSeconds]);

  return display;
}

function formatSeconds(totalSeconds: number): string {
  const rounded = Math.ceil(totalSeconds);
  const minutes = Math.floor(rounded / 60);
  const seconds = rounded % 60;
  return `${minutes}:${seconds.toString().padStart(2, "0")}`;
}

/**
 * Duration countdown for an active concentration (Fase 12) — rounds mode
 * decrements as the combat WS advances turns/rounds, seconds mode counts
 * down in real time client-side from `expires_at`. Renders nothing for
 * `mode: null` (not concentrating) or `"indefinite"` durations (no clock to
 * show). Highlights visually in the last moments before expiring.
 */
export function DurationCounter({
  remaining,
  currentRound = null,
}: {
  remaining: ConcentrationRemaining;
  /** Combat encounter's current round, from `useOptionalCombatContext` — `null` outside combat. */
  currentRound?: number | null;
}) {
  const roundsDisplay = useRoundsRemaining(remaining.remaining_rounds ?? 0, currentRound);
  const secondsDisplay = useSecondsRemaining(remaining.remaining_seconds ?? 0);

  if (remaining.mode === null) return null;

  if (remaining.mode === "indefinite") {
    return (
      <p className="text-xs text-muted-foreground" data-testid="duration-counter-indefinite">
        Duração indeterminada
      </p>
    );
  }

  if (remaining.mode === "rounds") {
    const isUrgent = roundsDisplay <= URGENT_ROUNDS_THRESHOLD;
    const isExpired = roundsDisplay <= 0;
    return (
      <p
        role={isUrgent ? "alert" : undefined}
        data-testid="duration-counter-rounds"
        className={
          isUrgent
            ? "animate-pulse text-xs font-semibold text-destructive"
            : "text-xs text-muted-foreground"
        }
      >
        {isExpired
          ? "Duração expirada"
          : `${roundsDisplay} ${roundsDisplay === 1 ? "rodada restante" : "rodadas restantes"}`}
      </p>
    );
  }

  // mode === "seconds"
  const isUrgent = secondsDisplay <= URGENT_SECONDS_THRESHOLD;
  const isExpired = secondsDisplay <= 0;
  return (
    <p
      role={isUrgent ? "alert" : undefined}
      data-testid="duration-counter-seconds"
      className={
        isUrgent
          ? "animate-pulse text-xs font-semibold text-destructive"
          : "text-xs text-muted-foreground"
      }
    >
      {isExpired ? "Duração expirada" : `${formatSeconds(secondsDisplay)} restantes`}
    </p>
  );
}
