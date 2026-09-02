/**
 * Correlates a `MapToken` with its `EncounterParticipant`, and vice versa —
 * there's no direct FK between the two domains (backend/app/maps and
 * backend/app/combat are deliberately decoupled, see
 * `MapService.tokens_in_radius`'s docstring), so the match is done by the
 * shared `character_id`/`npc_id`/`monster_id` business key client-side
 * (Fase 15 história 5, target selection from the map).
 */

import type { EncounterParticipant } from "@/types/combat";
import type { MapToken } from "@/types/map";

/** The EncounterParticipant a MapToken represents, if any is currently in combat. */
export function participantForToken(
  token: MapToken,
  participants: EncounterParticipant[],
): EncounterParticipant | null {
  return (
    participants.find(
      (p) =>
        (token.character_id !== null && p.character_id === token.character_id) ||
        (token.npc_id !== null && p.npc_id === token.npc_id) ||
        (token.monster_id !== null && p.monster_id === token.monster_id),
    ) ?? null
  );
}

/** The MapToken representing an EncounterParticipant, if it has one on `tokens`. */
export function tokenForParticipant(
  participant: EncounterParticipant,
  tokens: MapToken[],
): MapToken | null {
  return (
    tokens.find(
      (t) =>
        (participant.character_id !== null && t.character_id === participant.character_id) ||
        (participant.npc_id !== null && t.npc_id === participant.npc_id) ||
        (participant.monster_id !== null && t.monster_id === participant.monster_id),
    ) ?? null
  );
}
