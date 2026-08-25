import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

const useCombat = vi.fn();
vi.mock("@/hooks/use-combat", () => ({
  useCombat: () => useCombat(),
}));

import { TurnIndicator } from "./turn-indicator";

const baseParticipant = {
  id: "p-1",
  is_active: true,
  initiative: 15,
};

describe("TurnIndicator", () => {
  it("renders the advance-turn button once everyone has rolled initiative", () => {
    useCombat.mockReturnValue({
      encounter: {
        status: "active",
        current_round: 1,
        participants: [baseParticipant],
      },
      advanceTurn: vi.fn(),
    });

    render(<TurnIndicator />);

    expect(screen.getByText(/avançar turno/i)).toBeInTheDocument();
  });

  it("hides the advance-turn button while any active participant is missing initiative", () => {
    useCombat.mockReturnValue({
      encounter: {
        status: "active",
        current_round: 1,
        participants: [{ ...baseParticipant, initiative: null }],
      },
      advanceTurn: vi.fn(),
    });

    render(<TurnIndicator />);

    expect(screen.queryByText(/avançar turno/i)).not.toBeInTheDocument();
  });

  it("ignores inactive participants when checking for missing initiative", () => {
    useCombat.mockReturnValue({
      encounter: {
        status: "active",
        current_round: 1,
        participants: [{ ...baseParticipant, initiative: null, is_active: false }],
      },
      advanceTurn: vi.fn(),
    });

    render(<TurnIndicator />);

    expect(screen.getByText(/avançar turno/i)).toBeInTheDocument();
  });
});
