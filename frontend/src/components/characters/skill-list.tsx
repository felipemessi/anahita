import { RollButton } from "@/components/characters/roll-button";
import type { CharacterSkill } from "@/types/character";

export const SKILL_LABELS: Record<string, string> = {
  acrobatics: "Acrobacia",
  animal_handling: "Adestrar Animais",
  arcana: "Arcanismo",
  athletics: "Atletismo",
  deception: "Enganação",
  history: "História",
  insight: "Intuição",
  intimidation: "Intimidação",
  investigation: "Investigação",
  medicine: "Medicina",
  nature: "Natureza",
  perception: "Percepção",
  performance: "Atuação",
  persuasion: "Persuasão",
  religion: "Religião",
  sleight_of_hand: "Prestidigitação",
  stealth: "Furtividade",
  survival: "Sobrevivência",
};

/**
 * Skills with proficiency/expertise marks and computed bonus (PRD §9.3).
 * Clicking a skill's bonus rolls 1d20 + `skill.bonus`, which the backend
 * already computed with the proficiency bonus folded in (Fase 8) — the
 * dot/color highlight below is purely visual, it doesn't change what gets
 * rolled.
 */
export function SkillList({ skills }: { skills: CharacterSkill[] }) {
  return (
    <section aria-label="Perícias">
      <ul className="divide-y divide-border rounded-lg border border-border">
        {skills.map((skill) => {
          const label = SKILL_LABELS[skill.skill] ?? skill.skill;
          return (
            <li
              key={skill.id}
              className={`flex items-center justify-between px-3 py-2 text-sm ${
                skill.proficient ? "font-medium" : ""
              }`}
            >
              <span className="flex items-center gap-2">
                <span
                  aria-hidden="true"
                  className={`inline-block h-2 w-2 rounded-full ${
                    skill.expertise
                      ? "bg-primary"
                      : skill.proficient
                        ? "border border-primary bg-primary/40"
                        : "border border-border"
                  }`}
                />
                {label}
                {skill.expertise ? (
                  <span className="text-xs text-primary">(especialização)</span>
                ) : skill.proficient ? (
                  <span className="text-xs text-muted-foreground">(proficiente)</span>
                ) : null}
              </span>
              <RollButton
                label={label}
                modifier={skill.bonus}
                className="font-mono hover:text-primary hover:underline"
              />
            </li>
          );
        })}
      </ul>
    </section>
  );
}
