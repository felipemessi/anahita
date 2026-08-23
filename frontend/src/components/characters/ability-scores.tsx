import type { CharacterAbilityScore } from "@/types/character";

const ABILITY_LABELS: Record<string, string> = {
  str: "Força",
  dex: "Destreza",
  con: "Constituição",
  int: "Inteligência",
  wis: "Sabedoria",
  cha: "Carisma",
};

/** 2x3 grid of ability scores, modifiers and saving throws (PRD §9.3). */
export function AbilityScores({ scores }: { scores: CharacterAbilityScore[] }) {
  return (
    <section aria-label="Atributos" className="grid grid-cols-2 gap-3 sm:grid-cols-3">
      {scores.map((score) => (
        <div
          key={score.id}
          className="rounded-lg border border-border bg-card p-3 text-center"
        >
          <p className="text-xs uppercase text-muted-foreground">
            {ABILITY_LABELS[score.ability] ?? score.ability}
          </p>
          <p className="text-2xl font-bold">{score.base_score + score.asi_bonus + score.misc_bonus}</p>
          <p className="font-mono text-sm text-muted-foreground">
            {score.modifier >= 0 ? "+" : ""}
            {score.modifier}
          </p>
        </div>
      ))}
    </section>
  );
}
