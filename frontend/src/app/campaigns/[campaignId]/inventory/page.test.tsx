import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("next/navigation", () => ({
  useParams: () => ({ campaignId: "campaign-1" }),
}));

const useMyMembership = vi.fn();
vi.mock("@/hooks/use-campaign", () => ({
  useMyMembership: (...args: unknown[]) => useMyMembership(...args),
}));

const useCharacters = vi.fn();
vi.mock("@/hooks/use-character", () => ({
  useCharacters: (...args: unknown[]) => useCharacters(...args),
}));

const useCatalogList = vi.fn();
const useCatalogEntry = vi.fn();
vi.mock("@/hooks/use-catalog", () => ({
  useCatalogList: (...args: unknown[]) => useCatalogList(...args),
  useCatalogEntry: (...args: unknown[]) => useCatalogEntry(...args),
}));

const usePartyInventory = vi.fn();
const useCampaignLootDrops = vi.fn();
const useCampaignEncounters = vi.fn();
const useAddToInventory = vi.fn();
const useCreateLootDrop = vi.fn();
const useUpdateInventoryEntry = vi.fn();
const useRemoveFromInventory = vi.fn();
const useClaimLootDrop = vi.fn();
vi.mock("@/hooks/use-inventory", () => ({
  usePartyInventory: (...args: unknown[]) => usePartyInventory(...args),
  useCampaignLootDrops: (...args: unknown[]) => useCampaignLootDrops(...args),
  useCampaignEncounters: (...args: unknown[]) => useCampaignEncounters(...args),
  useAddToInventory: (...args: unknown[]) => useAddToInventory(...args),
  useCreateLootDrop: (...args: unknown[]) => useCreateLootDrop(...args),
  useUpdateInventoryEntry: (...args: unknown[]) => useUpdateInventoryEntry(...args),
  useRemoveFromInventory: (...args: unknown[]) => useRemoveFromInventory(...args),
  useClaimLootDrop: (...args: unknown[]) => useClaimLootDrop(...args),
}));

import InventoryPage from "./page";

describe("InventoryPage", () => {
  beforeEach(() => {
    useCharacters.mockReturnValue({ data: [] });
    useCatalogList.mockReturnValue({ data: [] });
    useCatalogEntry.mockReturnValue({ data: undefined });
    usePartyInventory.mockReturnValue({ data: [], isLoading: false });
    useCampaignLootDrops.mockReturnValue({ data: [], isLoading: false });
    useCampaignEncounters.mockReturnValue({ data: [] });
    useAddToInventory.mockReturnValue({ mutate: vi.fn(), isPending: false });
    useCreateLootDrop.mockReturnValue({ mutate: vi.fn(), isPending: false });
    useUpdateInventoryEntry.mockReturnValue({ mutate: vi.fn() });
    useRemoveFromInventory.mockReturnValue({ mutate: vi.fn() });
    useClaimLootDrop.mockReturnValue({ mutate: vi.fn(), isPending: false });
  });

  it("shows the management forms for the DM", () => {
    useMyMembership.mockReturnValue({ data: { id: "mem-1", role: "dm" } });
    render(<InventoryPage />);

    expect(
      screen.getByPlaceholderText(/buscar item no catálogo/i),
    ).toBeInTheDocument();
    expect(screen.getByText(/distribuir loot/i)).toBeInTheDocument();
  });

  it("hides the management forms for a player", () => {
    useMyMembership.mockReturnValue({ data: { id: "mem-2", role: "player" } });
    render(<InventoryPage />);

    expect(
      screen.queryByPlaceholderText(/buscar item no catálogo/i),
    ).not.toBeInTheDocument();
    expect(screen.queryByText(/distribuir loot/i)).not.toBeInTheDocument();
  });

  it("shows empty states when there is no inventory or loot", () => {
    useMyMembership.mockReturnValue({ data: { id: "mem-2", role: "player" } });
    render(<InventoryPage />);

    expect(screen.getByText(/inventário vazio/i)).toBeInTheDocument();
    expect(screen.getByText(/nenhum loot registrado/i)).toBeInTheDocument();
  });
});
