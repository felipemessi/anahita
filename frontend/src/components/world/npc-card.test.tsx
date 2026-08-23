import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const useNpcFactions = vi.fn();
const useNpcLocations = vi.fn();
const useNpcSessions = vi.fn();
const useCatalogEntry = vi.fn();

vi.mock("@/hooks/use-world", () => ({
  useNpcFactions: (...args: unknown[]) => useNpcFactions(...args),
  useNpcLocations: (...args: unknown[]) => useNpcLocations(...args),
  useNpcSessions: (...args: unknown[]) => useNpcSessions(...args),
}));
vi.mock("@/hooks/use-catalog", () => ({
  useCatalogEntry: (...args: unknown[]) => useCatalogEntry(...args),
}));
vi.mock("@/components/catalog/monster-stat-block", () => ({
  MonsterStatBlock: ({ monster }: { monster: { name: string } }) => (
    <div data-testid="stat-block">{monster.name}</div>
  ),
}));

import { NpcCard } from "./npc-card";

const NPC = {
  id: "npc-1",
  campaign_id: "campaign-1",
  name: "Innkeeper Tom",
  race: "Human",
  occupation: "Innkeeper",
  description: "Runs the inn",
  personality: null,
  is_alive: true,
  stat_block_id: null,
  created_at: "2026-01-01T00:00:00Z",
};

beforeEach(() => {
  useNpcFactions.mockReturnValue({ data: [] });
  useNpcLocations.mockReturnValue({ data: [] });
  useNpcSessions.mockReturnValue({ data: [] });
  useCatalogEntry.mockReturnValue({ data: undefined });
});

describe("NpcCard", () => {
  it("shows no stat block button when the NPC has no stat_block_id", () => {
    render(<NpcCard npc={NPC} />);

    expect(screen.getByText("Innkeeper Tom")).toBeInTheDocument();
    expect(screen.queryByText(/ver stat block/i)).not.toBeInTheDocument();
  });

  it("reveals the stat block on click when the NPC has a stat_block_id", () => {
    useCatalogEntry.mockReturnValue({ data: { name: "Goblin Boss" } });
    render(<NpcCard npc={{ ...NPC, stat_block_id: "monster-1" }} />);

    expect(screen.queryByTestId("stat-block")).not.toBeInTheDocument();
    fireEvent.click(screen.getByText(/ver stat block/i));
    expect(screen.getByTestId("stat-block")).toHaveTextContent("Goblin Boss");
  });
});
