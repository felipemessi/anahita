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

/** Skills with proficiency/expertise marks and computed bonus (PRD §9.3). */
export function SkillList({ skills }: { skills: CharacterSkill[] }) {
  return (
    <section aria-label="Perícias">
      <ul className="divide-y divide-border rounded-lg border border-border">
        {skills.map((skill) => (
          <li key={skill.id} className="flex items-center justify-between px-3 py-2 text-sm">
            <span>
              {SKILL_LABELS[skill.skill] ?? skill.skill}
              {skill.expertise ? (
                <span className="ml-2 text-xs text-primary">(especialização)</span>
              ) : skill.proficient ? (
                <span className="ml-2 text-xs text-muted-foreground">(proficiente)</span>
              ) : null}
            </span>
            <span className="font-mono">
              {skill.bonus >= 0 ? "+" : ""}
              {skill.bonus}
            </span>
          </li>
        ))}
      </ul>
    </section>
  );
}
