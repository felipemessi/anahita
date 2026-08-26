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
    vi.advanceTimersByTime(2500);
  });

  expect(screen.getByLabelText("Rolagens recentes")).toHaveTextContent("11 +5 = 16");
});
