import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const useCatalogList = vi.fn();
const useCatalogEntry = vi.fn();
vi.mock("@/hooks/use-catalog", () => ({
  useCatalogList: (...args: unknown[]) => useCatalogList(...args),
  useCatalogEntry: (...args: unknown[]) => useCatalogEntry(...args),
}));

const useAddCharacterEquipment = vi.fn();
const useUpdateCharacterEquipment = vi.fn();
const useRemoveCharacterEquipment = vi.fn();
const useWeaponAttackProfile = vi.fn();
vi.mock("@/hooks/use-character", () => ({
  useAddCharacterEquipment: () => useAddCharacterEquipment(),
  useUpdateCharacterEquipment: () => useUpdateCharacterEquipment(),
  useRemoveCharacterEquipment: () => useRemoveCharacterEquipment(),
  useWeaponAttackProfile: (...args: unknown[]) => useWeaponAttackProfile(...args),
}));

const useRoll = vi.fn();
const useRollDamage = vi.fn();
vi.mock("@/components/characters/roll-log", () => ({
  useRoll: () => useRoll(),
  useRollDamage: () => useRollDamage(),
}));

import { EquipmentList } from "./equipment-list";

const longswordEntry = {
  id: "entry-longsword",
  item_id: "item-longsword",
  equipped: false,
  quantity: 1,
  attunement: false,
};

const longswordItem = {
  id: "item-longsword",
  weapon_detail: { id: "wd-1", damage_dice: "1d8", damage_type: "slashing", weapon_range: "Melee" },
};

describe("EquipmentList", () => {
  const updateMutate = vi.fn();
  const removeMutate = vi.fn();
  const attackMutate = vi.fn();
  const roll = vi.fn();
  const rollDamage = vi.fn();

  beforeEach(() => {
    updateMutate.mockReset();
    removeMutate.mockReset();
    attackMutate.mockReset();
    roll.mockReset();
    rollDamage.mockReset();
    updateMutate.mockResolvedValue(undefined);
    removeMutate.mockResolvedValue(undefined);

    useAddCharacterEquipment.mockReturnValue({ mutateAsync: vi.fn(), isPending: false });
    useUpdateCharacterEquipment.mockReturnValue({
      mutateAsync: updateMutate,
      isPending: false,
    });
    useRemoveCharacterEquipment.mockReturnValue({
      mutateAsync: removeMutate,
      isPending: false,
    });
    useWeaponAttackProfile.mockReturnValue({ mutateAsync: attackMutate, isPending: false });
    useRoll.mockReturnValue(roll);
    useRollDamage.mockReturnValue(rollDamage);
    useCatalogEntry.mockReturnValue({ data: undefined, isLoading: false });
    useCatalogList.mockReturnValue({ data: [{ id: "item-longsword", name: "Longsword" }] });
  });

  it("toggling equipped calls the update mutation with the flipped value", () => {
    render(
      <EquipmentList characterId="char-1" campaignId="camp-1" equipment={[longswordEntry]} />,
    );

    fireEvent.click(screen.getByRole("button", { name: "equipar" }));

    expect(updateMutate).toHaveBeenCalledWith({
      equipmentId: "entry-longsword",
      data: { equipped: true },
    });
  });

  it("changing quantity calls the update mutation with the new value", () => {
    render(
      <EquipmentList characterId="char-1" campaignId="camp-1" equipment={[longswordEntry]} />,
    );

    fireEvent.change(screen.getByDisplayValue("1"), { target: { value: "3" } });

    expect(updateMutate).toHaveBeenCalledWith({
      equipmentId: "entry-longsword",
      data: { quantity: 3 },
    });
  });

  it("removing an item calls the remove mutation with its entry id", () => {
    render(
      <EquipmentList characterId="char-1" campaignId="camp-1" equipment={[longswordEntry]} />,
    );

    fireEvent.click(screen.getByRole("button", { name: "remover" }));

    expect(removeMutate).toHaveBeenCalledWith("entry-longsword");
  });

  it("shows no 'atacar' button for an unequipped weapon", () => {
    useCatalogEntry.mockReturnValue({ data: longswordItem, isLoading: false });
    render(
      <EquipmentList characterId="char-1" campaignId="camp-1" equipment={[longswordEntry]} />,
    );

    expect(screen.queryByRole("button", { name: "atacar" })).not.toBeInTheDocument();
  });

  it("shows no 'atacar' button for an equipped item that isn't a weapon", () => {
    useCatalogEntry.mockReturnValue({ data: { id: "item-longsword", weapon_detail: null }, isLoading: false });
    render(
      <EquipmentList
        characterId="char-1"
        campaignId="camp-1"
        equipment={[{ ...longswordEntry, equipped: true }]}
      />,
    );

    expect(screen.queryByRole("button", { name: "atacar" })).not.toBeInTheDocument();
  });

  it("clicking 'atacar' rolls only the attack, never the damage", async () => {
    useCatalogEntry.mockReturnValue({ data: longswordItem, isLoading: false });
    const profile = {
      weapon_name: "longsword",
      ability: "str",
      attack_bonus: 4,
      damage_dice: "1d8",
      damage_bonus: 2,
      damage_type: "slashing",
      proficient: true,
    };
    attackMutate.mockResolvedValue(profile);

    render(
      <EquipmentList
        characterId="char-1"
        campaignId="camp-1"
        equipment={[{ ...longswordEntry, equipped: true }]}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "atacar" }));

    expect(attackMutate).toHaveBeenCalledWith("entry-longsword");
    await vi.waitFor(() => expect(roll).toHaveBeenCalledWith("longsword (ataque)", 4));
    expect(rollDamage).not.toHaveBeenCalled();
  });

  it("clicking 'dano' rolls only the damage, never the attack", async () => {
    useCatalogEntry.mockReturnValue({ data: longswordItem, isLoading: false });
    const profile = {
      weapon_name: "longsword",
      ability: "str",
      attack_bonus: 4,
      damage_dice: "1d8",
      damage_bonus: 2,
      damage_type: "slashing",
      proficient: true,
    };
    attackMutate.mockResolvedValue(profile);

    render(
      <EquipmentList
        characterId="char-1"
        campaignId="camp-1"
        equipment={[{ ...longswordEntry, equipped: true }]}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "dano" }));

    expect(attackMutate).toHaveBeenCalledWith("entry-longsword");
    await vi.waitFor(() =>
      expect(rollDamage).toHaveBeenCalledWith("longsword (dano)", "1d8", 2),
    );
    expect(roll).not.toHaveBeenCalled();
  });
});
