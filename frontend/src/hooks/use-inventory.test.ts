import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import React from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const claimLootDrop = vi.fn();
vi.mock("@/lib/api/inventory", () => ({
  addToInventory: vi.fn(),
  claimLootDrop: (...args: unknown[]) => claimLootDrop(...args),
  createLootDrop: vi.fn(),
  listCampaignEncounters: vi.fn(),
  listCampaignLootDrops: vi.fn(),
  listPartyInventory: vi.fn(),
  removeFromInventory: vi.fn(),
  updateInventoryEntry: vi.fn(),
}));

import { CHARACTERS_QUERY_KEY } from "@/hooks/use-character";
import { LOOT_QUERY_KEY, useClaimLootDrop } from "./use-inventory";

function setup() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  const invalidateSpy = vi.spyOn(queryClient, "invalidateQueries");

  const wrapper = ({ children }: { children: React.ReactNode }) =>
    React.createElement(QueryClientProvider, { client: queryClient }, children);

  return { queryClient, wrapper, invalidateSpy };
}

describe("useClaimLootDrop", () => {
  beforeEach(() => {
    claimLootDrop.mockReset();
  });

  it("invalidates both the campaign loot feed and the claiming character's sheet", async () => {
    claimLootDrop.mockResolvedValue({ id: "drop-1", claimed_by: "char-2" });

    const { wrapper, invalidateSpy } = setup();
    const { result } = renderHook(() => useClaimLootDrop("campaign-1"), { wrapper });

    result.current.mutate({
      lootDropId: "drop-1",
      data: { character_id: "char-2" },
    });

    await waitFor(() => {
      expect(claimLootDrop).toHaveBeenCalledWith("drop-1", { character_id: "char-2" });
    });

    await waitFor(() => {
      expect(invalidateSpy).toHaveBeenCalledWith({
        queryKey: [...LOOT_QUERY_KEY, "campaign-1"],
      });
      expect(invalidateSpy).toHaveBeenCalledWith({
        queryKey: [...CHARACTERS_QUERY_KEY, "char-2"],
      });
    });
  });
});
