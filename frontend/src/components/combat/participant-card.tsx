import { RollButton } from "@/components/characters/roll-button";
import { useCatalogEntry } from "@/hooks/use-catalog";
import { useCharacter } from "@/hooks/use-character";
import { CONDITION_LABEL } from "@/lib/utils/conditions";
import { calculateModifier } from "@/lib/utils/dnd-rules";
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

      {participant.concentration_dc !== null ? (
        <ConcentrationSaveCallout participant={participant} dc={participant.concentration_dc} />
      ) : null}

      {children ? <div className="mt-3">{children}</div> : null}
    </li>
  );
}

/**
 * The CD text plus a click-to-roll CON save shortcut — the modifier comes
 * from the participant's own Character (its computed `save_bonus`, so
 * proficiency is already folded in) or, for a catalog monster, its raw
 * Constitution score (a monster's own saving-throw proficiency bonus isn't
 * resolved here, a documented simplification: `MonsterProficiency` only
 * points at a generic `Proficiency` row, not distinctly "CON save" vs.
 * anything else, without another catalog round-trip). A purely manual/NPC
 * participant with no resolvable score rolls at +0.
 */
function ConcentrationSaveCallout({
  participant,
  dc,
}: {
  participant: EncounterParticipant;
  dc: number;
}) {
  const { data: character } = useCharacter(participant.character_id ?? "");
  const { data: monster } = useCatalogEntry("monsters", participant.monster_id ?? "");
  const conModifier =
    character?.ability_scores.find((s) => s.ability === "con")?.save_bonus ??
    (monster ? calculateModifier(monster.constitution) : 0);

  return (
    <p role="alert" className="mt-2 flex items-center gap-2 text-xs font-medium text-amber-500">
      <span>Teste de concentração: CD {dc}</span>
      <RollButton
        label="Resistência de Constituição"
        modifier={conModifier}
        className="underline hover:text-foreground"
      />
    </p>
  );
}
