import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const useCatalogList = vi.fn();
const useCatalogEntry = vi.fn();
vi.mock("@/hooks/use-catalog", () => ({
  useCatalogList: (...args: unknown[]) => useCatalogList(...args),
  useCatalogEntry: (...args: unknown[]) => useCatalogEntry(...args),
}));

const useAddCharacterSpell = vi.fn();
const useUpdateCharacterSpell = vi.fn();
const useRemoveCharacterSpell = vi.fn();
vi.mock("@/hooks/use-character", () => ({
  useAddCharacterSpell: () => useAddCharacterSpell(),
  useUpdateCharacterSpell: () => useUpdateCharacterSpell(),
  useRemoveCharacterSpell: () => useRemoveCharacterSpell(),
}));

import { ApiError } from "@/lib/api/client";

import { SpellListByCircle } from "./spell-list-by-circle";

const wizardClass = { id: "wizard-id", index: "wizard", name: "Wizard" };
const characterClasses = [{ id: "cc-1", class_definition_id: "wizard-id", subclass_id: null, level: 1 }];

const cantripEntry = {
  id: "entry-cantrip",
  spell_id: "spell-fire-bolt",
  prepared: false,
  source_class: "wizard",
  level: 0,
  ritual: false,
};
const leveledEntry = {
  id: "entry-magic-missile",
  spell_id: "spell-magic-missile",
  prepared: true,
  source_class: "wizard",
  level: 1,
  ritual: false,
};

const catalogSpellSummaries = [
  { id: "spell-fire-bolt", name: "Fire Bolt", level: 0 },
  { id: "spell-magic-missile", name: "Magic Missile", level: 1 },
];

describe("SpellListByCircle", () => {
  const addSpellMutate = vi.fn();
  const updateSpellMutate = vi.fn();
  const removeSpellMutate = vi.fn();

  beforeEach(() => {
    addSpellMutate.mockReset();
    updateSpellMutate.mockReset();
    removeSpellMutate.mockReset();
    addSpellMutate.mockResolvedValue(undefined);
    updateSpellMutate.mockResolvedValue(undefined);
    removeSpellMutate.mockResolvedValue(undefined);

    useAddCharacterSpell.mockReturnValue({
      mutateAsync: addSpellMutate,
      isPending: false,
    });
    useUpdateCharacterSpell.mockReturnValue({
      mutateAsync: updateSpellMutate,
      isPending: false,
    });
    useRemoveCharacterSpell.mockReturnValue({
      mutateAsync: removeSpellMutate,
      isPending: false,
    });
    useCatalogEntry.mockReturnValue({ data: undefined, isLoading: false });
    useCatalogList.mockImplementation((category: string) => {
      if (category === "classes") return { data: [wizardClass] };
      if (category === "spells") return { data: catalogSpellSummaries };
      return { data: [] };
    });
  });

  it("groups known spells by circle, labeling 0 as Truques", () => {
    render(
      <SpellListByCircle
        characterId="char-1"
        campaignId="camp-1"
        spells={[cantripEntry, leveledEntry]}
        classes={characterClasses}
      />,
    );

    expect(screen.getByRole("heading", { name: "Truques" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "1º círculo" })).toBeInTheDocument();
    expect(screen.getByText("Fire Bolt")).toBeInTheDocument();
    expect(screen.getByText("Magic Missile")).toBeInTheDocument();
  });

  it("removing a spell calls the remove mutation with its entry id", async () => {
    render(
      <SpellListByCircle
        characterId="char-1"
        campaignId="camp-1"
        spells={[cantripEntry]}
        classes={characterClasses}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "remover" }));

    expect(removeSpellMutate).toHaveBeenCalledWith("entry-cantrip");
  });

  it("toggling prepared calls the update mutation with the flipped value", async () => {
    render(
      <SpellListByCircle
        characterId="char-1"
        campaignId="camp-1"
        spells={[cantripEntry]}
        classes={characterClasses}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "preparar" }));

    expect(updateSpellMutate).toHaveBeenCalledWith({
      spellEntryId: "entry-cantrip",
      data: { prepared: true },
    });
  });

  it("shows the backend's limit error instead of a generic message", async () => {
    addSpellMutate.mockRejectedValue(
      new ApiError(422, "wizard já prepara o máximo de 2 magias no nível 1 (2 preparadas)"),
    );
    useCatalogList.mockImplementation((category: string) => {
      if (category === "classes") return { data: [wizardClass] };
      if (category === "spells") return { data: catalogSpellSummaries };
      return { data: [] };
    });

    render(
      <SpellListByCircle
        characterId="char-1"
        campaignId="camp-1"
        spells={[]}
        classes={characterClasses}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /magic missile/i }));

    expect(
      await screen.findByText(/wizard já prepara o máximo de 2 magias no nível 1/),
    ).toBeInTheDocument();
  });
});
