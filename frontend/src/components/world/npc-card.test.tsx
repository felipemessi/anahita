import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const useNpcFactions = vi.fn();
const useNpcLocations = vi.fn();
const useNpcSessions = vi.fn();
const useLinkNpcSession = vi.fn();
const useCatalogEntry = vi.fn();
const useSessions = vi.fn();

vi.mock("@/hooks/use-world", () => ({
  useNpcFactions: (...args: unknown[]) => useNpcFactions(...args),
  useNpcLocations: (...args: unknown[]) => useNpcLocations(...args),
  useNpcSessions: (...args: unknown[]) => useNpcSessions(...args),
  useLinkNpcSession: (...args: unknown[]) => useLinkNpcSession(...args),
}));
vi.mock("@/hooks/use-catalog", () => ({
  useCatalogEntry: (...args: unknown[]) => useCatalogEntry(...args),
}));
vi.mock("@/hooks/use-session", () => ({
  useSessions: (...args: unknown[]) => useSessions(...args),
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
  useLinkNpcSession.mockReturnValue({ mutate: vi.fn(), isPending: false });
  useCatalogEntry.mockReturnValue({ data: undefined });
  useSessions.mockReturnValue({
    data: [{ id: "sess-1", session_number: 1, title: "The Beginning" }],
  });
});

describe("NpcCard", () => {
  it("shows no stat block button when the NPC has no stat_block_id", () => {
    render(<NpcCard npc={NPC} campaignId="campaign-1" />);

    expect(screen.getByText("Innkeeper Tom")).toBeInTheDocument();
    expect(screen.queryByText(/ver stat block/i)).not.toBeInTheDocument();
  });

  it("reveals the stat block on click when the NPC has a stat_block_id", () => {
    useCatalogEntry.mockReturnValue({ data: { name: "Goblin Boss" } });
    render(
      <NpcCard npc={{ ...NPC, stat_block_id: "monster-1" }} campaignId="campaign-1" />,
    );

    expect(screen.queryByTestId("stat-block")).not.toBeInTheDocument();
    fireEvent.click(screen.getByText(/ver stat block/i));
    expect(screen.getByTestId("stat-block")).toHaveTextContent("Goblin Boss");
  });

  it("hides the link-to-session control from non-DM viewers", () => {
    render(<NpcCard npc={NPC} campaignId="campaign-1" isDm={false} />);
    expect(screen.queryByText(/vincular a uma sessão/i)).not.toBeInTheDocument();
  });

  it("lets the DM link the NPC to a session appearance", () => {
    const mutate = vi.fn();
    useLinkNpcSession.mockReturnValue({ mutate, isPending: false });
    render(<NpcCard npc={NPC} campaignId="campaign-1" isDm={true} />);

    fireEvent.click(screen.getByText(/vincular a uma sessão/i));
    fireEvent.change(screen.getByLabelText(/sessão em que innkeeper tom apareceu/i), {
      target: { value: "sess-1" },
    });
    fireEvent.click(screen.getByRole("button", { name: /^vincular$/i }));

    expect(mutate).toHaveBeenCalledWith(
      { session_id: "sess-1" },
      expect.anything(),
    );
  });
});
