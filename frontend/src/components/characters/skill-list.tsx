import { RollButton } from "@/components/characters/roll-button";
import type { CharacterSkill } from "@/types/character";

const SKILL_LABELS: Record<string, string> = {
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
 * Clicking a skill's bonus rolls 1d20 + that bonus.
 */
export function SkillList({ skills }: { skills: CharacterSkill[] }) {
  return (
    <section aria-label="Perícias">
      <ul className="divide-y divide-border rounded-lg border border-border">
        {skills.map((skill) => {
          const label = SKILL_LABELS[skill.skill] ?? skill.skill;
          return (
            <li key={skill.id} className="flex items-center justify-between px-3 py-2 text-sm">
              <span>
                {label}
                {skill.expertise ? (
                  <span className="ml-2 text-xs text-primary">(especialização)</span>
                ) : skill.proficient ? (
                  <span className="ml-2 text-xs text-muted-foreground">(proficiente)</span>
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
