"use client";

import { useRoll } from "@/components/characters/roll-log";
import { formatModifier } from "@/lib/utils/dice";

/** A modifier/bonus rendered as a button that rolls 1d20 + the bonus on click. */
export function RollButton({
  label,
  modifier,
  className,
}: {
  label: string;
  modifier: number;
  className?: string;
}) {
  const roll = useRoll();

  return (
    <button
      type="button"
      onClick={() => roll(label, modifier)}
      aria-label={`Rolar ${label} (${formatModifier(modifier)})`}
      className={className}
    >
      {formatModifier(modifier)}
    </button>
  );
}
