"use client";

import { useCombat } from "@/hooks/use-combat";
import { ALL_CONDITIONS, CONDITION_LABEL } from "@/lib/utils/conditions";
import type { Condition, EncounterParticipant } from "@/types/combat";

/** Tap a condition to add it to the participant; tap an active one to remove it. */
export function ConditionBadges({
  participant,
}: {
  participant: EncounterParticipant;
}) {
  const { updateParticipant } = useCombat();
  const active = new Set(participant.conditions.map((c) => c.condition));

  function toggle(condition: Condition) {
    if (active.has(condition)) {
      updateParticipant(participant.id, { removeCondition: condition });
    } else {
      updateParticipant(participant.id, { addCondition: condition });
    }
  }

  return (
    <div className="flex flex-wrap gap-1">
      {ALL_CONDITIONS.map((condition) => {
        const isActive = active.has(condition);
        return (
          <button
            key={condition}
            type="button"
            onClick={() => toggle(condition)}
            aria-pressed={isActive}
            className={`rounded-full border px-2 py-0.5 text-xs transition-colors ${
              isActive
                ? "border-primary bg-primary/10 text-primary"
                : "border-border text-muted-foreground hover:bg-secondary"
            }`}
          >
            {CONDITION_LABEL[condition]}
          </button>
        );
      })}
    </div>
  );
}
