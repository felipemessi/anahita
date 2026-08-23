import { describe, expect, it, vi } from "vitest";

const apiFetch = vi.fn();
vi.mock("@/lib/api/client", () => ({
  apiFetch: (...args: unknown[]) => apiFetch(...args),
}));

import { addCharacterEquipment, addCharacterFeature, addCharacterSpell } from "./characters";

describe("characters API", () => {
  it("addCharacterSpell posts to /characters/{id}/spells", async () => {
    apiFetch.mockResolvedValueOnce({ id: "char-1" });

    await addCharacterSpell("char-1", { spell_id: "spell-1", prepared: true });

    expect(apiFetch).toHaveBeenCalledWith("/characters/char-1/spells", {
      method: "POST",
      body: JSON.stringify({ spell_id: "spell-1", prepared: true }),
    });
  });

  it("addCharacterEquipment posts to /characters/{id}/equipment", async () => {
    apiFetch.mockResolvedValueOnce({ id: "char-1" });

    await addCharacterEquipment("char-1", { item_id: "item-1" });

    expect(apiFetch).toHaveBeenCalledWith("/characters/char-1/equipment", {
      method: "POST",
      body: JSON.stringify({ item_id: "item-1" }),
    });
  });

  it("addCharacterFeature posts to /characters/{id}/features", async () => {
    apiFetch.mockResolvedValueOnce({ id: "char-1" });

    await addCharacterFeature("char-1", {
      source_type: "class",
      source_name: "Fighter",
      feature_name: "Second Wind",
    });

    expect(apiFetch).toHaveBeenCalledWith("/characters/char-1/features", {
      method: "POST",
      body: JSON.stringify({
        source_type: "class",
        source_name: "Fighter",
        feature_name: "Second Wind",
      }),
    });
  });
});
