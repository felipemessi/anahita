import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

const useCatalogEntry = vi.fn();
vi.mock("@/hooks/use-catalog", () => ({
  useCatalogEntry: (...args: unknown[]) => useCatalogEntry(...args),
}));

const useClaimLootDrop = vi.fn();
vi.mock("@/hooks/use-inventory", () => ({
  useClaimLootDrop: (...args: unknown[]) => useClaimLootDrop(...args),
}));

import { LootTable } from "./loot-table";
import type { LootDrop } from "@/types/inventory";

describe("LootTable", () => {
  const lootDrops: LootDrop[] = [
    {
      id: "drop-catalog",
      encounter_id: "enc-1",
      item_id: "item-1",
      magic_item_id: null,
      custom_item_name: null,
      quantity: 1,
      currency_cp: 0,
      claimed_by: null,
    },
    {
      id: "drop-magic",
      encounter_id: "enc-1",
      item_id: null,
      magic_item_id: "magic-1",
      custom_item_name: null,
      quantity: 1,
      currency_cp: 0,
      claimed_by: null,
    },
    {
      id: "drop-custom",
      encounter_id: "enc-1",
      item_id: null,
      magic_item_id: null,
      custom_item_name: "Rusty Dagger",
      quantity: 1,
      currency_cp: 500,
      claimed_by: "char-1",
    },
  ];

  it("renders catalog items, magic items, and custom items", () => {
    useCatalogEntry.mockImplementation((category: string, id: string) => {
      if (category === "equipment" && id === "item-1") {
        return { data: { name: "Longsword" } };
      }
      if (category === "magic-items" && id === "magic-1") {
        return { data: { name: "Ring of Protection" } };
      }
      return { data: undefined };
    });
    useClaimLootDrop.mockReturnValue({ mutate: vi.fn(), isPending: false });

    render(
      <LootTable lootDrops={lootDrops} campaignId="campaign-1" myCharacterId="char-2" />,
    );

    expect(screen.getByText("Longsword")).toBeInTheDocument();
    expect(screen.getByText("Ring of Protection")).toBeInTheDocument();
    expect(screen.getByText("Rusty Dagger")).toBeInTheDocument();
    expect(screen.getByText("reivindicado")).toBeInTheDocument();
  });

  it("hides the claim button for an unclaimed drop when the viewer has no character", () => {
    useCatalogEntry.mockReturnValue({ data: undefined });
    useClaimLootDrop.mockReturnValue({ mutate: vi.fn(), isPending: false });

    render(
      <LootTable
        lootDrops={[lootDrops[0] as LootDrop]}
        campaignId="campaign-1"
        myCharacterId={null}
      />,
    );

    expect(
      screen.queryByRole("button", { name: /reivindicar/i }),
    ).not.toBeInTheDocument();
  });

  it("shows a claim button for an unclaimed drop when the viewer has a character", () => {
    useCatalogEntry.mockReturnValue({ data: undefined });
    useClaimLootDrop.mockReturnValue({ mutate: vi.fn(), isPending: false });

    render(
      <LootTable
        lootDrops={[lootDrops[0] as LootDrop]}
        campaignId="campaign-1"
        myCharacterId="char-2"
      />,
    );

    expect(screen.getByRole("button", { name: /reivindicar/i })).toBeInTheDocument();
  });

  it("renders an empty state when there is no loot", () => {
    useCatalogEntry.mockReturnValue({ data: undefined });
    useClaimLootDrop.mockReturnValue({ mutate: vi.fn(), isPending: false });

    render(<LootTable lootDrops={[]} campaignId="campaign-1" myCharacterId={null} />);

    expect(screen.getByText(/nenhum loot registrado/i)).toBeInTheDocument();
  });
});
