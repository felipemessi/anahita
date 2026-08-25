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
vi.mock("@/hooks/use-character", () => ({
  useAddCharacterEquipment: () => useAddCharacterEquipment(),
  useUpdateCharacterEquipment: () => useUpdateCharacterEquipment(),
  useRemoveCharacterEquipment: () => useRemoveCharacterEquipment(),
}));

import { EquipmentList } from "./equipment-list";

const longswordEntry = {
  id: "entry-longsword",
  item_id: "item-longsword",
  equipped: false,
  quantity: 1,
  attunement: false,
};

describe("EquipmentList", () => {
  const updateMutate = vi.fn();
  const removeMutate = vi.fn();

  beforeEach(() => {
    updateMutate.mockReset();
    removeMutate.mockReset();
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
});
