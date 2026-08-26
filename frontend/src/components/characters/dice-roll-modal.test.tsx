import { act, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";

import { DiceRollModal, type DiceRollRequest } from "./dice-roll-modal";

beforeEach(() => {
  vi.useFakeTimers();
});

afterEach(() => {
  vi.useRealTimers();
  vi.restoreAllMocks();
});

const request: DiceRollRequest = {
  label: "Dado de vida (Fighter)",
  rollResult: 7,
  modifier: 2,
  total: 9,
};

it("renders nothing when there is no pending roll", () => {
  const { container } = render(<DiceRollModal request={null} onComplete={vi.fn()} />);
  expect(container).toBeEmptyDOMElement();
});

it("animates for ~1s before locking to the real result, then auto-closes after 5s", () => {
  vi.spyOn(Math, "random").mockReturnValue(0.99);
  const onComplete = vi.fn();
  render(<DiceRollModal request={request} onComplete={onComplete} />);

  expect(screen.getByRole("dialog", { name: "Rolando Dado de vida (Fighter)" })).toBeInTheDocument();
  // Still spinning: the final "die + modifier = total" line isn't shown yet.
  expect(screen.queryByText("7 +2 =")).not.toBeInTheDocument();

  act(() => {
    vi.advanceTimersByTime(1000);
  });

  expect(screen.getByText((_, el) => el?.textContent === "7 +2 = 9")).toBeInTheDocument();
  expect(onComplete).not.toHaveBeenCalled();

  act(() => {
    vi.advanceTimersByTime(5000);
  });

  expect(onComplete).toHaveBeenCalledTimes(1);
});

it("clicking Fechar dismisses the result before the 5s hold elapses", () => {
  vi.spyOn(Math, "random").mockReturnValue(0.99);
  const onComplete = vi.fn();
  render(<DiceRollModal request={request} onComplete={onComplete} />);

  act(() => {
    vi.advanceTimersByTime(1000);
  });

  fireEvent.click(screen.getByRole("button", { name: "Fechar" }));

  expect(onComplete).toHaveBeenCalledTimes(1);
});
