import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("next/navigation", () => ({
  useParams: () => ({ campaignId: "camp-1", encounterId: "enc-1" }),
}));

const useMyMembership = vi.fn();
vi.mock("@/hooks/use-campaign", () => ({
  useMyMembership: (...args: unknown[]) => useMyMembership(...args),
}));

const useCombat = vi.fn();
vi.mock("@/hooks/use-combat", () => ({
  useCombat: () => useCombat(),
}));

vi.mock("@/hooks/use-character", () => ({
  useCharacter: () => ({ data: undefined }),
}));

vi.mock("@/hooks/use-catalog", () => ({
  useCatalogEntry: () => ({ data: undefined }),
  useCatalogList: () => ({ data: undefined }),
}));

vi.mock("@/hooks/use-world", () => ({
  useNpcs: () => ({ data: undefined }),
}));

import CombatPage from "./page";

const baseEncounter = {
  id: "enc-1",
  session_id: "sess-1",
  name: "Emboscada na estrada",
  status: "active" as const,
  current_round: 1,
  current_turn_order: 0,
  created_at: "2026-01-01T00:00:00Z",
  participants: [
    {
      id: "p-1",
      encounter_id: "enc-1",
      character_id: "char-1",
      npc_id: null,
      name: "Aria",
      initiative: 15,
      hit_point_max: 20,
      hit_point_current: 20,
      temporary_hit_points: 0,
      armor_class: 14,
      turn_order: 0,
      is_active: true,
      conditions: [],
      effects: [],
    },
  ],
};

describe("CombatPage", () => {
  beforeEach(() => {
    useCombat.mockReturnValue({
      encounter: baseEncounter,
      isConnected: true,
      lastError: null,
      actionLog: [],
      removeParticipant: vi.fn(),
    });
  });

  it("player sees no DM action controls, only the read-only tracker", () => {
    useMyMembership.mockReturnValue({ data: { role: "player" } });

    render(<CombatPage />);

    expect(screen.getByText("Aria")).toBeInTheDocument();
    expect(screen.queryByText(/avançar turno/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/adicionar participante/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/remover participante/i)).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "-5" })).not.toBeInTheDocument();
    expect(screen.getByText(/modo espectador/i)).toBeInTheDocument();
  });

  it("DM sees the action controls the player doesn't", () => {
    useMyMembership.mockReturnValue({ data: { role: "dm" } });

    render(<CombatPage />);

    expect(screen.getByText(/avançar turno/i)).toBeInTheDocument();
    expect(screen.getByText(/adicionar participante/i)).toBeInTheDocument();
    expect(screen.getByText(/remover participante/i)).toBeInTheDocument();
    expect(screen.queryByText(/modo espectador/i)).not.toBeInTheDocument();
  });

  it("player's UI updates from the WebSocket-driven state without any action on their part", () => {
    useMyMembership.mockReturnValue({ data: { role: "player" } });

    const { rerender } = render(<CombatPage />);
    expect(screen.getByText(/20\/20/)).toBeInTheDocument();

    // Simulates what CombatProvider does when a `participant_updated` frame
    // arrives — the player never touched anything, the prop just changed.
    useCombat.mockReturnValue({
      encounter: {
        ...baseEncounter,
        participants: [
          { ...baseEncounter.participants[0], hit_point_current: 12 },
        ],
      },
      isConnected: true,
      lastError: null,
      actionLog: [],
      removeParticipant: vi.fn(),
    });
    rerender(<CombatPage />);

    expect(screen.getByText(/12\/20/)).toBeInTheDocument();
  });
});
