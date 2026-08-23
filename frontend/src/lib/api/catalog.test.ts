import { describe, expect, it, vi } from "vitest";

const apiFetch = vi.fn();
vi.mock("@/lib/api/client", () => ({
  apiFetch: (...args: unknown[]) => apiFetch(...args),
}));

import { createCustomEntry } from "./catalog";

describe("createCustomEntry", () => {
  it("always scopes the entry to the current campaign as is_custom=true", async () => {
    apiFetch.mockResolvedValueOnce({ id: "monster-1" });

    await createCustomEntry("monsters", "camp-1", { name: "Homebrew Beast" });

    expect(apiFetch).toHaveBeenCalledWith("/catalog/monsters", {
      method: "POST",
      body: JSON.stringify({
        name: "Homebrew Beast",
        is_custom: true,
        campaign_id: "camp-1",
      }),
    });
  });
});
