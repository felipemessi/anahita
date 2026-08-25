import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

const useCombat = vi.fn();
vi.mock("@/hooks/use-combat", () => ({
  useCombat: () => useCombat(),
}));

import { ActionLog } from "./action-log";

describe("ActionLog", () => {
  it("renders nothing when there are no resolved actions yet", () => {
    useCombat.mockReturnValue({ actionLog: [] });
    const { container } = render(<ActionLog />);
    expect(container).toBeEmptyDOMElement();
  });

  it("renders each resolved action's description, most recent first", () => {
    useCombat.mockReturnValue({
      actionLog: [
        { description: "Aldric attacks Goblin: 18 vs AC 15 — hit, dealing 6 damage" },
        { description: "Aldric rolled initiative: 15" },
      ],
    });

    render(<ActionLog />);

    const items = screen.getAllByRole("listitem");
    expect(items[0]).toHaveTextContent("Aldric attacks Goblin");
    expect(items[1]).toHaveTextContent("Aldric rolled initiative: 15");
  });
});
