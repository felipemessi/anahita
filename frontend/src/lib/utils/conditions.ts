import type { Condition } from "@/types/combat";

/**
 * Portuguese display labels for the 15 D&D 5e conditions — shared between
 * `participant-card.tsx` (read-only badges) and `condition-badges.tsx`
 * (the DM's toggle control) so the two never drift apart.
 */
export const CONDITION_LABEL: Record<Condition, string> = {
  blinded: "Cego",
  charmed: "Enfeitiçado",
  deafened: "Surdo",
  exhaustion: "Exaustão",
  frightened: "Amedrontado",
  grappled: "Agarrado",
  incapacitated: "Incapacitado",
  invisible: "Invisível",
  paralyzed: "Paralisado",
  petrified: "Petrificado",
  poisoned: "Envenenado",
  prone: "Caído",
  restrained: "Contido",
  stunned: "Atordoado",
  unconscious: "Inconsciente",
};

export const ALL_CONDITIONS = Object.keys(CONDITION_LABEL) as Condition[];
