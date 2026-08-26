import { act, fireEvent, render, screen, within } from "@testing-library/react";
import { useState } from "react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";

import { StepAbilityScores } from "./step-ability-scores";
import { INITIAL_WIZARD_STATE, type WizardState } from "./wizard-state";

/** Minimal stateful host so the controlled step can actually update. */
function Host() {
  const [state, setState] = useState<WizardState>(INITIAL_WIZARD_STATE);
  return (
    <StepAbilityScores
      value={state}
      onChange={(patch) => setState((prev) => ({ ...prev, ...patch }))}
    />
  );
}

beforeEach(() => {
  vi.useFakeTimers();
});

afterEach(() => {
  vi.useRealTimers();
  vi.restoreAllMocks();
});

it("standard array: assigning a value removes it from the other abilities' options", () => {
  render(<Host />);

  fireEvent.change(screen.getByLabelText("Força"), { target: { value: "15" } });

  const dexSelect = screen.getByLabelText("Destreza") as HTMLSelectElement;
  const options = within(dexSelect)
    .getAllByRole("option")
    .map((o) => (o as HTMLOptionElement).value);
  expect(options).not.toContain("15");
  expect(options).toContain("14");
});

it("point buy: blocks spending past the 27-point budget", () => {
  render(<Host />);

  fireEvent.click(screen.getByRole("radio", { name: "Compra de pontos" }));

  // 8 -> 15 costs 9 points each; three abilities at 15 spends the full 27.
  for (const label of ["Força", "Destreza", "Constituição"]) {
    for (let i = 0; i < 7; i++) {
      fireEvent.click(screen.getByRole("button", { name: `Aumentar ${label}` }));
    }
  }

  expect(screen.getByText("27/27 gastos")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Aumentar Inteligência" })).toBeDisabled();
});

it("roll: generates 6 values from 4d6-drop-lowest, assignable like the standard array", () => {
  vi.spyOn(Math, "random").mockReturnValue(0.5); // each d6 = 4, so 4d6-drop-lowest = 12

  render(<Host />);

  fireEvent.click(screen.getByRole("radio", { name: "Rolagem" }));
  fireEvent.click(screen.getByRole("button", { name: "Rolar atributos" }));

  act(() => {
    vi.advanceTimersByTime(2500);
  });

  const strSelect = screen.getByLabelText("Força") as HTMLSelectElement;
  const options = within(strSelect)
    .getAllByRole("option")
    .map((o) => (o as HTMLOptionElement).value);
  expect(options).toContain("12");
  expect(options).not.toContain("15"); // not the standard array
});
