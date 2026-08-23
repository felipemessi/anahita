import type { Encounter, EncounterParticipant } from "@/types/combat";

import { ParticipantCard } from "./participant-card";

/**
 * Ordered list of an encounter's participants, highlighting whoever's turn
 * it currently is. `renderActions` lets the DM view inject per-participant
 * controls (damage dialog, condition toggles, remove — história 3) without
 * this component needing to know about them; the read-only player view
 * (história 4) simply omits the prop.
 */
export function InitiativeTracker({
  encounter,
  renderActions,
}: {
  encounter: Encounter;
  renderActions?: (participant: EncounterParticipant) => React.ReactNode;
}) {
  const ordered = [...encounter.participants].sort(
    (a, b) => a.turn_order - b.turn_order,
  );

  if (ordered.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">
        Nenhum participante adicionado ainda.
      </p>
    );
  }

  return (
    <ul className="space-y-2">
      {ordered.map((participant) => (
        <ParticipantCard
          key={participant.id}
          participant={participant}
          isCurrentTurn={
            encounter.status === "active" &&
            participant.turn_order === encounter.current_turn_order
          }
        >
          {renderActions?.(participant)}
        </ParticipantCard>
      ))}
    </ul>
  );
}
