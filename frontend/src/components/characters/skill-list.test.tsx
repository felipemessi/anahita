import { act, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";

import { RollLogPanel, RollLogProvider } from "./roll-log";
import { SkillList } from "./skill-list";

const skills = [
  {
    id: "skill-athletics",
    skill: "athletics" as const,
    ability: "str" as const,
    proficient: true,
    expertise: false,
    bonus: 5,
  },
];

const mixedSkills = [
  { id: "skill-arcana", skill: "arcana" as const, ability: "int" as const, proficient: false, expertise: false, bonus: 1 },
  { id: "skill-athletics", skill: "athletics" as const, ability: "str" as const, proficient: true, expertise: false, bonus: 5 },
  { id: "skill-stealth", skill: "stealth" as const, ability: "dex" as const, proficient: true, expertise: true, bonus: 8 },
];

beforeEach(() => {
  vi.useFakeTimers();
});

afterEach(() => {
  vi.useRealTimers();
  vi.restoreAllMocks();
});

it("clicking a skill's bonus rolls 1d20 + the bonus, after the roll animation", () => {
  vi.spyOn(Math, "random").mockReturnValue(0.5); // die = 11
  render(
    <RollLogProvider>
      <SkillList skills={skills} />
      <RollLogPanel />
    </RollLogProvider>,
  );

  fireEvent.click(screen.getByRole("button", { name: "Rolar Atletismo (+5)" }));
  act(() => {
    vi.advanceTimersByTime(6500);
  });

  expect(screen.getByLabelText("Rolagens recentes")).toHaveTextContent("11 +5 = 16");
});

it("renders a proficiency/expertise highlight, and rolls the full computed bonus", () => {
  render(
    <RollLogProvider>
      <SkillList skills={mixedSkills} />
    </RollLogProvider>,
  );

  const arcanaRow = screen.getByText("Arcanismo").closest("li");
  const athleticsRow = screen.getByText("Atletismo").closest("li");
  const stealthRow = screen.getByText("Furtividade").closest("li");

  expect(arcanaRow).not.toHaveTextContent("proficiente");
  expect(athleticsRow).toHaveTextContent("(proficiente)");
  expect(stealthRow).toHaveTextContent("(especialização)");

  // The roll uses CharacterSkillRead.bonus (already includes proficiency),
  // not a client-recomputed ability modifier.
  expect(screen.getByRole("button", { name: "Rolar Furtividade (+8)" })).toBeInTheDocument();
});
