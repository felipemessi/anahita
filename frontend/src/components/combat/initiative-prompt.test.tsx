import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const useCombat = vi.fn();
vi.mock("@/hooks/use-combat", () => ({
  useCombat: () => useCombat(),
}));

import { InitiativePrompt } from "./initiative-prompt";

const baseParticipant = {
  id: "p-1",
  encounter_id: "enc-1",
  character_id: "char-1",
  npc_id: null,
  monster_id: null,
  name: "Aldric",
  hit_point_max: 20,
  hit_point_current: 20,
  temporary_hit_points: 0,
  armor_class: 14,
  turn_order: 0,
  is_active: true,
  conditions: [],
  effects: [],
};

describe("InitiativePrompt", () => {
  const rollInitiative = vi.fn();

  beforeEach(() => {
    rollInitiative.mockReset();
  });

  it("renders nothing when every active participant already rolled", () => {
    useCombat.mockReturnValue({
      encounter: {
        status: "active",
        participants: [{ ...baseParticipant, initiative: 15 }],
      },
      rollInitiative,
    });

    const { container } = render(<InitiativePrompt />);
    expect(container).toBeEmptyDOMElement();
  });

  it("lists participants still missing initiative", () => {
    useCombat.mockReturnValue({
      encounter: {
        status: "active",
        participants: [
          { ...baseParticipant, initiative: null },
          { ...baseParticipant, id: "p-2", name: "Goblin", initiative: 10 },
        ],
      },
      rollInitiative,
    });

    render(<InitiativePrompt />);

    expect(screen.getByText("Aldric")).toBeInTheDocument();
    expect(screen.queryByText("Goblin")).not.toBeInTheDocument();
  });

  it("clicking rolls initiative for that participant", () => {
    useCombat.mockReturnValue({
      encounter: {
        status: "active",
        participants: [{ ...baseParticipant, initiative: null }],
      },
      rollInitiative,
    });

    render(<InitiativePrompt />);
    fireEvent.click(screen.getByRole("button", { name: "Rolar iniciativa" }));

    expect(rollInitiative).toHaveBeenCalledWith("p-1");
  });

  it("ignores inactive participants missing initiative", () => {
    useCombat.mockReturnValue({
      encounter: {
        status: "active",
        participants: [{ ...baseParticipant, initiative: null, is_active: false }],
      },
      rollInitiative,
    });

    const { container } = render(<InitiativePrompt />);
    expect(container).toBeEmptyDOMElement();
  });
});
