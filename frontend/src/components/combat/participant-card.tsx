import { CONDITION_LABEL } from "@/lib/utils/conditions";
import type { EncounterParticipant } from "@/types/combat";

/**
 * One combatant's card: name, HP bar, AC badge, condition badges, and a
 * highlight when it's this participant's turn.
 */
export function ParticipantCard({
  participant,
  isCurrentTurn,
  children,
}: {
  participant: EncounterParticipant;
  isCurrentTurn: boolean;
  /** DM-only action controls (damage dialog, condition toggles, remove) — omitted in the read-only player view. */
  children?: React.ReactNode;
}) {
  const hpRatio = Math.max(
    0,
    Math.min(1, participant.hit_point_current / Math.max(1, participant.hit_point_max)),
  );
  const hpColor =
    hpRatio > 0.5 ? "bg-emerald-500" : hpRatio > 0.2 ? "bg-amber-500" : "bg-destructive";

  return (
    <li
      className={`rounded-lg border px-4 py-3 transition-colors ${
        isCurrentTurn
          ? "border-primary bg-primary/10"
          : "border-border bg-card"
      } ${!participant.is_active ? "opacity-50" : ""}`}
    >
      <div className="flex items-center justify-between gap-2">
        <span className="font-medium">{participant.name}</span>
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <span className="rounded-full border border-border px-2 py-0.5">
            CA {participant.armor_class}
          </span>
          <span className="font-mono">Iniciativa {participant.initiative}</span>
        </div>
      </div>

      <div className="mt-2 flex items-center gap-2">
        <div className="h-2 flex-1 overflow-hidden rounded-full bg-secondary">
          <div
            className={`h-full ${hpColor}`}
            style={{ width: `${hpRatio * 100}%` }}
          />
        </div>
        <span className="font-mono text-xs text-muted-foreground">
          {participant.hit_point_current}/{participant.hit_point_max}
          {participant.temporary_hit_points > 0
            ? ` (+${participant.temporary_hit_points})`
            : ""}
        </span>
      </div>

      {participant.conditions.length > 0 ? (
        <div className="mt-2 flex flex-wrap gap-1">
          {participant.conditions.map((condition) => (
            <span
              key={condition.id}
              className="rounded-full bg-secondary px-2 py-0.5 text-xs text-secondary-foreground"
            >
              {CONDITION_LABEL[condition.condition] ?? condition.condition}
            </span>
          ))}
        </div>
      ) : null}

      {children ? <div className="mt-3">{children}</div> : null}
    </li>
  );
}
