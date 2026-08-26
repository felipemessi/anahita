import { act, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";

import { RollLogPanel, RollLogProvider, useRoll } from "./roll-log";

beforeEach(() => {
  vi.useFakeTimers();
});

afterEach(() => {
  vi.useRealTimers();
  vi.restoreAllMocks();
});

function RollTrigger() {
  const roll = useRoll();
  return (
    <button type="button" onClick={() => roll("Força", 3)}>
      Rolar
    </button>
  );
}

it("shows the roll animation before the result lands in the log, wherever RollLogPanel is placed", () => {
  vi.spyOn(Math, "random").mockReturnValue(0.5); // die = 11
  render(
    <RollLogProvider>
      <section>Conteúdo da ficha</section>
      <RollTrigger />
      <RollLogPanel />
    </RollLogProvider>,
  );

  expect(screen.queryByLabelText("Rolagens recentes")).not.toBeInTheDocument();

  fireEvent.click(screen.getByRole("button", { name: "Rolar" }));

  // Animation is running: the roll dialog is up, but not yet in the log.
  expect(screen.getByRole("dialog", { name: "Rolando Força" })).toBeInTheDocument();
  expect(screen.queryByLabelText("Rolagens recentes")).not.toBeInTheDocument();

  act(() => {
    vi.advanceTimersByTime(6500);
  });

  expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  expect(screen.getByLabelText("Rolagens recentes")).toHaveTextContent("11 +3 = 14");
});

it("keeps RollLogPanel positioned after content placed before it, mirroring a footer layout", () => {
  vi.spyOn(Math, "random").mockReturnValue(0.5);
  render(
    <RollLogProvider>
      <section data-testid="sheet-content">Conteúdo da ficha</section>
      <RollTrigger />
      <RollLogPanel />
    </RollLogProvider>,
  );

  fireEvent.click(screen.getByRole("button", { name: "Rolar" }));
  act(() => {
    vi.advanceTimersByTime(6500);
  });

  const content = screen.getByTestId("sheet-content");
  const panel = screen.getByLabelText("Rolagens recentes");
  // DOCUMENT_POSITION_FOLLOWING (4) means `panel` comes after `content` in the tree.
  expect(content.compareDocumentPosition(panel) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
});
