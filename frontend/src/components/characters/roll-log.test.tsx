import { act, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";

import { RollLogPanel, RollLogProvider, useRoll, useRollDamage } from "./roll-log";

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

function DamageTrigger() {
  const rollDamage = useRollDamage();
  return (
    <button type="button" onClick={() => rollDamage("Longsword (dano)", "1d8", 2)}>
      Dano
    </button>
  );
}

it("rolls damage on its own, independent of any attack roll", () => {
  vi.spyOn(Math, "random").mockReturnValue(0.5); // 1d8 -> 5
  render(
    <RollLogProvider>
      <DamageTrigger />
      <RollLogPanel />
    </RollLogProvider>,
  );

  expect(screen.queryByRole("dialog")).not.toBeInTheDocument();

  fireEvent.click(screen.getByRole("button", { name: "Dano" }));

  expect(screen.getByRole("dialog", { name: "Rolando Longsword (dano)" })).toBeInTheDocument();

  act(() => {
    vi.advanceTimersByTime(6500);
  });

  expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  expect(screen.getByLabelText("Rolagens recentes")).toHaveTextContent("5 +2 = 7");
});

it("queues an attack roll and a damage roll fired back to back without clobbering each other", () => {
  vi.spyOn(Math, "random").mockReturnValue(0.5); // d20 -> 11, d8 -> 5

  function BothTriggers() {
    const roll = useRoll();
    const rollDamage = useRollDamage();
    return (
      <>
        <button type="button" onClick={() => roll("Longsword (ataque)", 4)}>
          Atacar
        </button>
        <button type="button" onClick={() => rollDamage("Longsword (dano)", "1d8", 2)}>
          Dano
        </button>
      </>
    );
  }

  render(
    <RollLogProvider>
      <BothTriggers />
      <RollLogPanel />
    </RollLogProvider>,
  );

  fireEvent.click(screen.getByRole("button", { name: "Atacar" }));
  fireEvent.click(screen.getByRole("button", { name: "Dano" }));

  // Only the attack roll (fired first) is animating; damage is queued.
  expect(screen.getByRole("dialog", { name: "Rolando Longsword (ataque)" })).toBeInTheDocument();

  act(() => {
    vi.advanceTimersByTime(6500);
  });

  expect(screen.getByRole("dialog", { name: "Rolando Longsword (dano)" })).toBeInTheDocument();

  act(() => {
    vi.advanceTimersByTime(6500);
  });

  expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  const log = screen.getByLabelText("Rolagens recentes");
  expect(log).toHaveTextContent("11 +4 = 15");
  expect(log).toHaveTextContent("5 +2 = 7");
});
