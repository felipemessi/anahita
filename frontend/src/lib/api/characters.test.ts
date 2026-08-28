import { describe, expect, it, vi } from "vitest";

const apiFetch = vi.fn();
vi.mock("@/lib/api/client", () => ({
  apiFetch: (...args: unknown[]) => apiFetch(...args),
}));

import {
  addCharacterEquipment,
  addCharacterFeature,
  addCharacterSpell,
  getSpellAttackProfile,
  getWeaponAttackProfile,
} from "./characters";

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

  it("getWeaponAttackProfile gets /characters/{id}/equipment/{id}/attack-profile", async () => {
    apiFetch.mockResolvedValueOnce({ attack_bonus: 4 });

    await getWeaponAttackProfile("char-1", "entry-1");

    expect(apiFetch).toHaveBeenCalledWith(
      "/characters/char-1/equipment/entry-1/attack-profile",
    );
  });

  it("getSpellAttackProfile gets /characters/{id}/spells/{id}/attack-profile", async () => {
    apiFetch.mockResolvedValueOnce({ action_type: "attack_roll" });

    await getSpellAttackProfile("char-1", "entry-1");

    expect(apiFetch).toHaveBeenCalledWith(
      "/characters/char-1/spells/entry-1/attack-profile",
    );
  });

  it("getSpellAttackProfile appends cast_at_level when given", async () => {
    apiFetch.mockResolvedValueOnce({ action_type: "saving_throw" });

    await getSpellAttackProfile("char-1", "entry-1", 3);

    expect(apiFetch).toHaveBeenCalledWith(
      "/characters/char-1/spells/entry-1/attack-profile?cast_at_level=3",
    );
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
