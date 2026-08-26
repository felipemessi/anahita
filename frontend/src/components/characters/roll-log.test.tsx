import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";

import { RollLogPanel, RollLogProvider, useRoll } from "./roll-log";

afterEach(() => {
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

it("renders the recent-rolls log wherever RollLogPanel is placed, after a roll", () => {
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

  expect(screen.getByLabelText("Rolagens recentes")).toHaveTextContent("11 +3 = 14");
});

it("keeps RollLogPanel positioned after content placed before it, mirroring a footer layout", () => {
  vi.spyOn(Math, "random").mockReturnValue(0.5);
  const { container } = render(
    <RollLogProvider>
      <section data-testid="sheet-content">Conteúdo da ficha</section>
      <RollTrigger />
      <RollLogPanel />
    </RollLogProvider>,
  );

  fireEvent.click(screen.getByRole("button", { name: "Rolar" }));

  const content = screen.getByTestId("sheet-content");
  const panel = screen.getByLabelText("Rolagens recentes");
  // DOCUMENT_POSITION_FOLLOWING (4) means `panel` comes after `content` in the tree.
  expect(content.compareDocumentPosition(panel) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  expect(container).toBeInTheDocument();
});
