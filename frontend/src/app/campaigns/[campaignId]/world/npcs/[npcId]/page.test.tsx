import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

vi.mock("next/navigation", () => ({
  useParams: () => ({ campaignId: "campaign-1", npcId: "npc-1" }),
}));

const useNpcs = vi.fn();
const useNpcFactions = vi.fn();
const useNpcLocations = vi.fn();
const useNpcSessions = vi.fn();
const useFactions = vi.fn();
const useLocations = vi.fn();
vi.mock("@/hooks/use-world", () => ({
  useNpcs: (...args: unknown[]) => useNpcs(...args),
  useNpcFactions: (...args: unknown[]) => useNpcFactions(...args),
  useNpcLocations: (...args: unknown[]) => useNpcLocations(...args),
  useNpcSessions: (...args: unknown[]) => useNpcSessions(...args),
  useFactions: (...args: unknown[]) => useFactions(...args),
  useLocations: (...args: unknown[]) => useLocations(...args),
}));

const useCatalogEntry = vi.fn();
vi.mock("@/hooks/use-catalog", () => ({
  useCatalogEntry: (...args: unknown[]) => useCatalogEntry(...args),
}));

const useSessions = vi.fn();
vi.mock("@/hooks/use-session", () => ({
  useSessions: (...args: unknown[]) => useSessions(...args),
}));

vi.mock("@/components/catalog/monster-stat-block", () => ({
  MonsterStatBlock: ({ monster }: { monster: { name: string } }) => (
    <div data-testid="stat-block">{monster.name}</div>
  ),
}));

import NpcDetailPage from "./page";

describe("NpcDetailPage", () => {
  it("shows the NPC's faction role, location presence, and session appearance", () => {
    useNpcs.mockReturnValue({
      data: [
        {
          id: "npc-1",
          campaign_id: "campaign-1",
          name: "Volo",
          race: "Human",
          occupation: "Explorer",
          description: "A wandering chronicler",
          personality: null,
          is_alive: true,
          stat_block_id: null,
          created_at: "2026-01-01T00:00:00Z",
        },
      ],
      isLoading: false,
    });
    useNpcFactions.mockReturnValue({
      data: [{ id: "link-1", npc_id: "npc-1", faction_id: "fac-1", role_in_faction: "Spymaster" }],
    });
    useNpcLocations.mockReturnValue({
      data: [{ id: "link-2", npc_id: "npc-1", location_id: "loc-1", presence_type: "resides" }],
    });
    useNpcSessions.mockReturnValue({
      data: [{ id: "link-3", npc_id: "npc-1", session_id: "sess-1", appearance_note: "Gave a quest" }],
    });
    useFactions.mockReturnValue({ data: [{ id: "fac-1", name: "Harpers" }] });
    useLocations.mockReturnValue({ data: [{ id: "loc-1", name: "Waterdeep" }] });
    useSessions.mockReturnValue({
      data: [{ id: "sess-1", session_number: 1, title: "The Beginning" }],
    });
    useCatalogEntry.mockReturnValue({ data: undefined });

    render(<NpcDetailPage />);

    expect(screen.getByText("Volo")).toBeInTheDocument();
    expect(screen.getByText(/harpers/i)).toHaveTextContent("Harpers — Spymaster");
    expect(screen.getByText(/waterdeep/i)).toHaveTextContent("Waterdeep (reside)");
    expect(screen.getByText(/sessão 1/i)).toHaveTextContent("Gave a quest");
  });
});
