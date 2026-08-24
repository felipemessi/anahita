import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

const useCatalogEntry = vi.fn();
vi.mock("@/hooks/use-catalog", () => ({
  useCatalogEntry: (...args: unknown[]) => useCatalogEntry(...args),
}));

const useUpdateInventoryEntry = vi.fn();
const useRemoveFromInventory = vi.fn();
vi.mock("@/hooks/use-inventory", () => ({
  useUpdateInventoryEntry: (...args: unknown[]) => useUpdateInventoryEntry(...args),
  useRemoveFromInventory: (...args: unknown[]) => useRemoveFromInventory(...args),
}));

import { ItemCard } from "./item-card";
import type { PartyInventoryEntry } from "@/types/inventory";

const entry: PartyInventoryEntry = {
  id: "entry-1",
  campaign_id: "campaign-1",
  item_id: "item-1",
  quantity: 3,
  notes: null,
};

describe("ItemCard", () => {
  it("shows the resolved catalog item name and quantity", () => {
    useCatalogEntry.mockReturnValue({ data: { name: "Longsword" }, isLoading: false });
    useUpdateInventoryEntry.mockReturnValue({ mutate: vi.fn() });
    useRemoveFromInventory.mockReturnValue({ mutate: vi.fn() });

    render(<ItemCard entry={entry} campaignId="campaign-1" isDm={false} />);

    expect(screen.getByText("Longsword")).toBeInTheDocument();
    expect(screen.getByText("x3")).toBeInTheDocument();
  });

  it("shows quantity edit and remove controls only for the DM", () => {
    useCatalogEntry.mockReturnValue({ data: { name: "Longsword" }, isLoading: false });
    useUpdateInventoryEntry.mockReturnValue({ mutate: vi.fn() });
    useRemoveFromInventory.mockReturnValue({ mutate: vi.fn() });

    render(<ItemCard entry={entry} campaignId="campaign-1" isDm />);

    expect(screen.getByRole("spinbutton")).toBeInTheDocument();
    expect(screen.getByText("remover")).toBeInTheDocument();
  });
});
