import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("next/navigation", () => ({
  useParams: () => ({ campaignId: "campaign-1" }),
}));

const useMyMembership = vi.fn();
vi.mock("@/hooks/use-campaign", () => ({
  useMyMembership: (...args: unknown[]) => useMyMembership(...args),
}));

const useNpcs = vi.fn();
const useCreateNpc = vi.fn();
const useRevealNpc = vi.fn();
vi.mock("@/hooks/use-world", () => ({
  useNpcs: (...args: unknown[]) => useNpcs(...args),
  useCreateNpc: (...args: unknown[]) => useCreateNpc(...args),
  useNpcFactions: () => ({ data: [] }),
  useNpcLocations: () => ({ data: [] }),
  useNpcSessions: () => ({ data: [] }),
  useLinkNpcSession: () => ({ mutate: vi.fn(), isPending: false }),
  useRevealNpc: (...args: unknown[]) => useRevealNpc(...args),
}));

const useCatalogList = vi.fn();
const useCatalogEntry = vi.fn();
vi.mock("@/hooks/use-catalog", () => ({
  useCatalogList: (...args: unknown[]) => useCatalogList(...args),
  useCatalogEntry: (...args: unknown[]) => useCatalogEntry(...args),
}));

vi.mock("@/hooks/use-session", () => ({
  useSessions: () => ({ data: [] }),
}));

import NpcsPage from "./page";

const HIDDEN_NPC = {
  id: "npc-hidden",
  campaign_id: "campaign-1",
  name: "Shadow Broker",
  race: "Human",
  occupation: null,
  description: "",
  personality: null,
  is_alive: true,
  stat_block_id: null,
  is_revealed: false,
  created_at: "2026-01-01T00:00:00Z",
};

const REVEALED_NPC = {
  ...HIDDEN_NPC,
  id: "npc-revealed",
  name: "Innkeeper Tom",
  is_revealed: true,
};

describe("NpcsPage", () => {
  const mutate = vi.fn();

  beforeEach(() => {
    mutate.mockClear();
    useNpcs.mockReturnValue({ data: [], isLoading: false });
    useMyMembership.mockReturnValue({ data: { role: "dm" } });
    useCreateNpc.mockReturnValue({ mutate, isPending: false, isError: false });
    useRevealNpc.mockReturnValue({ mutate: vi.fn(), isPending: false });
    useCatalogList.mockReturnValue({
      data: [{ id: "monster-1", name: "Goblin", challenge_rating: 0.25 }],
    });
    useCatalogEntry.mockReturnValue({ data: undefined });
  });

  it("creates an NPC with a stat block picked from the monster catalog", () => {
    render(<NpcsPage />);

    fireEvent.change(screen.getByPlaceholderText("Nome"), {
      target: { value: "Grukk" },
    });
    fireEvent.change(screen.getByPlaceholderText("Raça"), {
      target: { value: "Goblin" },
    });
    fireEvent.change(
      screen.getByPlaceholderText(/buscar stat block no catálogo/i),
      { target: { value: "Gob" } },
    );
    fireEvent.click(screen.getByText("Goblin", { selector: "span" }));

    fireEvent.click(screen.getByRole("button", { name: /criar npc/i }));

    expect(mutate).toHaveBeenCalledWith(
      expect.objectContaining({
        name: "Grukk",
        race: "Goblin",
        stat_block_id: "monster-1",
      }),
      expect.anything(),
    );
  });

  it("creates an NPC without a stat block when none is picked", () => {
    render(<NpcsPage />);

    fireEvent.change(screen.getByPlaceholderText("Nome"), {
      target: { value: "Innkeeper Tom" },
    });
    fireEvent.change(screen.getByPlaceholderText("Raça"), {
      target: { value: "Human" },
    });
    fireEvent.click(screen.getByRole("button", { name: /criar npc/i }));

    expect(mutate).toHaveBeenCalledWith(
      expect.objectContaining({ stat_block_id: null }),
      expect.anything(),
    );
  });

  it("lets the DM see and reveal a hidden NPC", () => {
    useNpcs.mockReturnValue({ data: [HIDDEN_NPC, REVEALED_NPC], isLoading: false });

    render(<NpcsPage />);

    expect(screen.getByText("Shadow Broker")).toBeInTheDocument();
    expect(screen.getByText("Oculto")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /revelar/i })).toBeInTheDocument();
  });

  it("only shows revealed NPCs to a player (server already filters hidden ones)", () => {
    useMyMembership.mockReturnValue({ data: { role: "player" } });
    // Non-DM callers never receive hidden NPCs from the API — simulate that here.
    useNpcs.mockReturnValue({ data: [REVEALED_NPC], isLoading: false });

    render(<NpcsPage />);

    expect(screen.getByText("Innkeeper Tom")).toBeInTheDocument();
    expect(screen.queryByText("Shadow Broker")).not.toBeInTheDocument();
    expect(screen.queryByText("Oculto")).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /revelar/i })).not.toBeInTheDocument();
  });
});
