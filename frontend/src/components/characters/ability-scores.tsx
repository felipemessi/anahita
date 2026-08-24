import { RollButton } from "@/components/characters/roll-button";
import type { CharacterAbilityScore } from "@/types/character";

const ABILITY_LABELS: Record<string, string> = {
  str: "Força",
  dex: "Destreza",
  con: "Constituição",
  int: "Inteligência",
  wis: "Sabedoria",
  cha: "Carisma",
};

/**
 * 2x3 grid of ability scores, modifiers and saving throws (PRD §9.3).
 * Clicking the modifier or the saving throw rolls 1d20 + that bonus.
 */
export function AbilityScores({ scores }: { scores: CharacterAbilityScore[] }) {
  return (
    <section aria-label="Atributos" className="grid grid-cols-2 gap-3 sm:grid-cols-3">
      {scores.map((score) => {
        const label = ABILITY_LABELS[score.ability] ?? score.ability;
        return (
          <div
            key={score.id}
            className="rounded-lg border border-border bg-card p-3 text-center"
          >
            <p className="text-xs uppercase text-muted-foreground">{label}</p>
            <p className="text-2xl font-bold">
              {score.base_score + score.asi_bonus + score.misc_bonus}
            </p>
            <RollButton
              label={label}
              modifier={score.modifier}
              className="font-mono text-sm text-muted-foreground hover:text-foreground hover:underline"
            />
            <p className="mt-1 text-[11px] uppercase text-muted-foreground">
              Resistência
              {score.save_proficient ? <span className="ml-1 text-primary">●</span> : null}
            </p>
            <RollButton
              label={`Resistência de ${label}`}
              modifier={score.save_bonus}
              className="font-mono text-xs text-muted-foreground hover:text-foreground hover:underline"
            />
          </div>
        );
      })}
    </section>
  );
}
