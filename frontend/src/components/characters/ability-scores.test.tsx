import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";

import { AbilityScores } from "./ability-scores";
import { RollLogProvider } from "./roll-log";

const scores = [
  {
    id: "score-str",
    ability: "str" as const,
    base_score: 16,
    asi_bonus: 0,
    misc_bonus: 0,
    modifier: 3,
    save_proficient: true,
    save_bonus: 5,
  },
  {
    id: "score-dex",
    ability: "dex" as const,
    base_score: 14,
    asi_bonus: 0,
    misc_bonus: 0,
    modifier: 2,
    save_proficient: false,
    save_bonus: 2,
  },
];

afterEach(() => {
  vi.restoreAllMocks();
});

it("clicking an ability modifier rolls 1d20 + the modifier", () => {
  vi.spyOn(Math, "random").mockReturnValue(0.5); // die = 11
  render(
    <RollLogProvider>
      <AbilityScores scores={scores} />
    </RollLogProvider>,
  );

  fireEvent.click(screen.getByRole("button", { name: "Rolar Força (+3)" }));

  expect(screen.getByLabelText("Rolagens recentes")).toHaveTextContent("11 +3 = 14");
});

it("clicking a saving throw rolls 1d20 + the save bonus", () => {
  vi.spyOn(Math, "random").mockReturnValue(0); // die = 1
  render(
    <RollLogProvider>
      <AbilityScores scores={scores} />
    </RollLogProvider>,
  );

  fireEvent.click(screen.getByRole("button", { name: "Rolar Resistência de Força (+5)" }));

  expect(screen.getByLabelText("Rolagens recentes")).toHaveTextContent("1 +5 = 6");
});

it("marks proficient saving throws visually", () => {
  render(
    <RollLogProvider>
      <AbilityScores scores={scores} />
    </RollLogProvider>,
  );

  const strCard = screen.getByText("Força").closest("div");
  expect(strCard).toHaveTextContent("●");
  const dexCard = screen.getByText("Destreza").closest("div");
  expect(dexCard).not.toHaveTextContent("●");
});
