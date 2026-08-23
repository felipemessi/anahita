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
vi.mock("@/hooks/use-world", () => ({
  useNpcs: (...args: unknown[]) => useNpcs(...args),
  useCreateNpc: (...args: unknown[]) => useCreateNpc(...args),
  useNpcFactions: () => ({ data: [] }),
  useNpcLocations: () => ({ data: [] }),
  useNpcSessions: () => ({ data: [] }),
}));

const useCatalogList = vi.fn();
const useCatalogEntry = vi.fn();
vi.mock("@/hooks/use-catalog", () => ({
  useCatalogList: (...args: unknown[]) => useCatalogList(...args),
  useCatalogEntry: (...args: unknown[]) => useCatalogEntry(...args),
}));

import NpcsPage from "./page";

describe("NpcsPage", () => {
  const mutate = vi.fn();

  beforeEach(() => {
    mutate.mockClear();
    useNpcs.mockReturnValue({ data: [], isLoading: false });
    useMyMembership.mockReturnValue({ data: { role: "dm" } });
    useCreateNpc.mockReturnValue({ mutate, isPending: false, isError: false });
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
});
