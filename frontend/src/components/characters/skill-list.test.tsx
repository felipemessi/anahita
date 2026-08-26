import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";

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

afterEach(() => {
  vi.restoreAllMocks();
});

it("clicking a skill's bonus rolls 1d20 + the bonus", () => {
  vi.spyOn(Math, "random").mockReturnValue(0.5); // die = 11
  render(
    <RollLogProvider>
      <SkillList skills={skills} />
      <RollLogPanel />
    </RollLogProvider>,
  );

  fireEvent.click(screen.getByRole("button", { name: "Rolar Atletismo (+5)" }));

  expect(screen.getByLabelText("Rolagens recentes")).toHaveTextContent("11 +5 = 16");
});
