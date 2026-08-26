import { act, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const useCombat = vi.fn();
vi.mock("@/hooks/use-combat", () => ({
  useCombat: () => useCombat(),
}));

import { ActionLog } from "./action-log";

const baseEntry = {
  actor_id: "p-1",
  target_id: "p-2",
  action_type: "attack_weapon" as const,
  attack_roll: null,
  attack_bonus: null,
  hit: null,
  damage_rolled: null,
  damage_type: null,
  condition_applied: null,
  attacker_check: null,
  target_check: null,
  concentration_dc: null,
};

beforeEach(() => {
  vi.useFakeTimers();
});

afterEach(() => {
  vi.useRealTimers();
  vi.restoreAllMocks();
});

describe("ActionLog", () => {
  it("renders nothing when there are no resolved actions yet", () => {
    useCombat.mockReturnValue({ actionLog: [] });
    const { container } = render(<ActionLog />);
    expect(container).toBeEmptyDOMElement();
  });

  it("renders each resolved action's description, most recent first", () => {
    useCombat.mockReturnValue({
      actionLog: [
        { ...baseEntry, description: "Aldric attacks Goblin: 18 vs AC 15 — hit, dealing 6 damage" },
        { ...baseEntry, description: "Aldric rolled initiative: 15" },
      ],
    });

    render(<ActionLog />);

    const items = screen.getAllByRole("listitem");
    expect(items[0]).toHaveTextContent("Aldric attacks Goblin");
    expect(items[1]).toHaveTextContent("Aldric rolled initiative: 15");
  });

  it("a resolved attack with a roll animates the attack, then the damage, before settling", () => {
    useCombat.mockReturnValue({
      actionLog: [
        {
          ...baseEntry,
          attack_roll: 18,
          attack_bonus: 5,
          hit: true,
          damage_rolled: 7,
          description: "Aldric attacks Goblin: 23 vs AC 15 — hit, dealing 7 damage",
        },
      ],
    });

    render(<ActionLog />);

    expect(screen.getByRole("dialog", { name: "Rolando Ataque" })).toBeInTheDocument();

    act(() => {
      vi.advanceTimersByTime(2500); // settle + hold + close the attack roll
    });
    expect(screen.getByRole("dialog", { name: "Rolando Dano" })).toBeInTheDocument();

    act(() => {
      vi.advanceTimersByTime(2500);
    });
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("a flavor action with no roll doesn't open the dice modal", () => {
    useCombat.mockReturnValue({
      actionLog: [{ ...baseEntry, description: "Aldric takes the dash action" }],
    });

    render(<ActionLog />);

    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });
});
