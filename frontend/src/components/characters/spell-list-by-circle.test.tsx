import { fireEvent, render, screen, waitFor } from "@testing-library/react";
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
const useCastCharacterSpell = vi.fn();
const useSpellAttackProfile = vi.fn();
vi.mock("@/hooks/use-character", () => ({
  useAddCharacterSpell: () => useAddCharacterSpell(),
  useUpdateCharacterSpell: () => useUpdateCharacterSpell(),
  useRemoveCharacterSpell: () => useRemoveCharacterSpell(),
  useCastCharacterSpell: () => useCastCharacterSpell(),
  useSpellAttackProfile: (...args: unknown[]) => useSpellAttackProfile(...args),
}));

const useRoll = vi.fn();
const useRollDamage = vi.fn();
vi.mock("@/components/characters/roll-log", () => ({
  useRoll: () => useRoll(),
  useRollDamage: () => useRollDamage(),
}));

import { ApiError } from "@/lib/api/client";

import { SpellListByCircle } from "./spell-list-by-circle";

const wizardClass = { id: "wizard-id", index: "wizard", name: "Wizard" };
const characterClasses = [
  { id: "cc-1", class_definition_id: "wizard-id", subclass_id: null, level: 1, hit_dice_used: 0 },
];

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
  { id: "spell-fire-bolt", name: "Fire Bolt", level: 0, classes: [{ id: "wizard-id", name: "Wizard" }] },
  { id: "spell-magic-missile", name: "Magic Missile", level: 1, classes: [{ id: "wizard-id", name: "Wizard" }] },
];

describe("SpellListByCircle", () => {
  const addSpellMutate = vi.fn();
  const updateSpellMutate = vi.fn();
  const removeSpellMutate = vi.fn();
  const castSpellMutate = vi.fn();
  // Populated per-test to control what `SpellRollControls` sees for a
  // given spell's catalog entry (`action_type`/`damages`) — see `useCatalogEntry` mock below.
  let catalogSpellDetailsById: Record<string, { action_type: string; damages: unknown[] }> = {};

  beforeEach(() => {
    addSpellMutate.mockReset();
    updateSpellMutate.mockReset();
    removeSpellMutate.mockReset();
    castSpellMutate.mockReset();
    addSpellMutate.mockResolvedValue(undefined);
    updateSpellMutate.mockResolvedValue(undefined);
    removeSpellMutate.mockResolvedValue(undefined);
    castSpellMutate.mockResolvedValue(undefined);

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
    useCastCharacterSpell.mockReturnValue({
      mutateAsync: castSpellMutate,
      isPending: false,
    });
    useSpellAttackProfile.mockReturnValue({ mutateAsync: vi.fn(), isPending: false });
    useRoll.mockReturnValue(vi.fn());
    useRollDamage.mockReturnValue(vi.fn());
    catalogSpellDetailsById = {};
    useCatalogEntry.mockImplementation((category: string, id: string) => {
      if (category === "classes" && id === "wizard-id") {
        return {
          data: {
            id: "wizard-id",
            index: "wizard",
            name: "Wizard",
            hit_die: 6,
            primary_ability: "int",
            saving_throw_proficiencies: "Intelligence, Wisdom",
            is_custom: false,
            levels: [
              {
                id: "wizard-level-1",
                level: 1,
                proficiency_bonus: 2,
                ability_score_bonuses: null,
                features: [],
                resources: [],
                spell_slots: [{ id: "slot-1", spell_level: 1, slot_count: 2 }],
              },
            ],
            subclasses: [],
          },
        };
      }
      if (category === "spells" && catalogSpellDetailsById[id]) {
        return { data: catalogSpellDetailsById[id], isLoading: false };
      }
      return { data: undefined, isLoading: false };
    });
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
        spellSlots={[]}
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
        spellSlots={[]}
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
        spellSlots={[]}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "preparar" }));

    await waitFor(() =>
      expect(updateSpellMutate).toHaveBeenCalledWith({
        spellEntryId: "entry-cantrip",
        data: { prepared: true },
      }),
    );
  });

  it("toggling one spell's prepared flag doesn't affect any other spell in the list", async () => {
    render(
      <SpellListByCircle
        characterId="char-1"
        campaignId="camp-1"
        spells={[cantripEntry, leveledEntry]}
        classes={characterClasses}
        spellSlots={[]}
      />,
    );

    // cantripEntry is unprepared ("preparar"), leveledEntry is prepared
    // ("preparada") — click only the unprepared one.
    fireEvent.click(screen.getByRole("button", { name: "preparar" }));

    await waitFor(() => expect(updateSpellMutate).toHaveBeenCalledTimes(1));
    expect(updateSpellMutate).toHaveBeenCalledWith({
      spellEntryId: "entry-cantrip",
      data: { prepared: true },
    });
    // The other spell's button is untouched — still "preparada", not
    // flipped or disabled by the first click's in-flight state.
    expect(screen.getByRole("button", { name: "preparada" })).toBeEnabled();
  });

  it("adding a spell within the class's available circle adds it directly, no confirmation", async () => {
    render(
      <SpellListByCircle
        characterId="char-1"
        campaignId="camp-1"
        spells={[]}
        classes={characterClasses}
        spellSlots={[]}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /magic missile/i }));

    await waitFor(() =>
      expect(addSpellMutate).toHaveBeenCalledWith({
        spell_id: "spell-magic-missile",
        source_class: "wizard",
      }),
    );
    expect(screen.queryByRole("alertdialog")).not.toBeInTheDocument();
  });

  it("adding a spell above the class's available circle asks for confirmation first", async () => {
    useCatalogList.mockImplementation((category: string) => {
      if (category === "classes") return { data: [wizardClass] };
      if (category === "spells") {
        return { data: [...catalogSpellSummaries, { id: "spell-fireball", name: "Fireball", level: 3, classes: [] }] };
      }
      return { data: [] };
    });

    render(
      <SpellListByCircle
        characterId="char-1"
        campaignId="camp-1"
        spells={[]}
        classes={characterClasses}
        spellSlots={[]}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /fireball/i }));

    expect(screen.getByRole("alertdialog", { name: "Círculo indisponível" })).toBeInTheDocument();
    expect(addSpellMutate).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole("button", { name: "Adicionar mesmo assim" }));

    await waitFor(() =>
      expect(addSpellMutate).toHaveBeenCalledWith({
        spell_id: "spell-fireball",
        source_class: "wizard",
      }),
    );
  });

  it("cancelling the circle-confirmation modal doesn't add the spell", () => {
    useCatalogList.mockImplementation((category: string) => {
      if (category === "classes") return { data: [wizardClass] };
      if (category === "spells") {
        return { data: [...catalogSpellSummaries, { id: "spell-fireball", name: "Fireball", level: 3, classes: [] }] };
      }
      return { data: [] };
    });

    render(
      <SpellListByCircle
        characterId="char-1"
        campaignId="camp-1"
        spells={[]}
        classes={characterClasses}
        spellSlots={[]}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /fireball/i }));
    fireEvent.click(screen.getByRole("button", { name: "Cancelar" }));

    expect(screen.queryByRole("alertdialog")).not.toBeInTheDocument();
    expect(addSpellMutate).not.toHaveBeenCalled();
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
        spellSlots={[]}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /magic missile/i }));

    expect(
      await screen.findByText(/wizard já prepara o máximo de 2 magias no nível 1/),
    ).toBeInTheDocument();
  });

  it("casting a leveled spell with an available slot calls cast at its own level", () => {
    render(
      <SpellListByCircle
        characterId="char-1"
        campaignId="camp-1"
        spells={[leveledEntry]}
        classes={characterClasses}
        spellSlots={[{ spell_level: 1, used: 0, max: 2 }]}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "conjurar" }));

    expect(castSpellMutate).toHaveBeenCalledWith({
      spellEntryId: "entry-magic-missile",
      data: { cast_at_level: 1 },
    });
  });

  it("disables the cast button with no slot available", () => {
    render(
      <SpellListByCircle
        characterId="char-1"
        campaignId="camp-1"
        spells={[leveledEntry]}
        classes={characterClasses}
        spellSlots={[{ spell_level: 1, used: 2, max: 2 }]}
      />,
    );

    expect(screen.getByRole("button", { name: "conjurar" })).toBeDisabled();
  });

  it("casting a ritual spell doesn't require an available slot", () => {
    render(
      <SpellListByCircle
        characterId="char-1"
        campaignId="camp-1"
        spells={[{ ...leveledEntry, ritual: true }]}
        classes={characterClasses}
        spellSlots={[{ spell_level: 1, used: 2, max: 2 }]}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "conjurar como ritual" }));

    expect(castSpellMutate).toHaveBeenCalledWith({
      spellEntryId: "entry-magic-missile",
      data: { as_ritual: true },
    });
  });

  it("upcasting selects and casts at a higher available slot level", () => {
    render(
      <SpellListByCircle
        characterId="char-1"
        campaignId="camp-1"
        spells={[leveledEntry]}
        classes={characterClasses}
        spellSlots={[
          { spell_level: 1, used: 0, max: 1 },
          { spell_level: 2, used: 0, max: 1 },
        ]}
      />,
    );

    fireEvent.change(screen.getByLabelText(/nível de conjuração/i), {
      target: { value: "2" },
    });
    fireEvent.click(screen.getByRole("button", { name: "conjurar" }));

    expect(castSpellMutate).toHaveBeenCalledWith({
      spellEntryId: "entry-magic-missile",
      data: { cast_at_level: 2 },
    });
  });

  it("casting with only a higher slot available than the spell's own level uses it", () => {
    render(
      <SpellListByCircle
        characterId="char-1"
        campaignId="camp-1"
        spells={[leveledEntry]}
        classes={characterClasses}
        spellSlots={[
          { spell_level: 1, used: 1, max: 1 },
          { spell_level: 2, used: 0, max: 1 },
        ]}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "conjurar" }));

    expect(castSpellMutate).toHaveBeenCalledWith({
      spellEntryId: "entry-magic-missile",
      data: { cast_at_level: 2 },
    });
  });

  it("shows 'atacar' and 'dano' for an attack_roll cantrip, each rolled independently", async () => {
    catalogSpellDetailsById["spell-fire-bolt"] = {
      action_type: "attack_roll",
      damages: [{ id: "d1" }],
    };
    const attackProfileMutate = vi.fn().mockResolvedValue({
      spell_name: "fire-bolt",
      action_type: "attack_roll",
      attack_bonus: 5,
      save_dc: null,
      save_ability: null,
      damage_dice: "1d10",
      damage_type: "fire",
    });
    useSpellAttackProfile.mockReturnValue({ mutateAsync: attackProfileMutate, isPending: false });
    const roll = vi.fn();
    const rollDamage = vi.fn();
    useRoll.mockReturnValue(roll);
    useRollDamage.mockReturnValue(rollDamage);

    render(
      <SpellListByCircle
        characterId="char-1"
        campaignId="camp-1"
        spells={[cantripEntry]}
        classes={characterClasses}
        spellSlots={[]}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "atacar" }));
    expect(attackProfileMutate).toHaveBeenCalledWith({
      spellEntryId: "entry-cantrip",
      castAtLevel: 0,
    });
    await waitFor(() => expect(roll).toHaveBeenCalledWith("Fire Bolt (ataque)", 5));
    expect(rollDamage).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole("button", { name: "dano" }));
    await waitFor(() =>
      expect(rollDamage).toHaveBeenCalledWith("Fire Bolt (dano)", "1d10", 0),
    );
  });

  it("shows 'ver CD' (not 'atacar') for a saving_throw spell, revealing the DC on click", async () => {
    catalogSpellDetailsById["spell-magic-missile"] = {
      action_type: "saving_throw",
      damages: [{ id: "d1" }],
    };
    const attackProfileMutate = vi.fn().mockResolvedValue({
      spell_name: "magic-missile",
      action_type: "saving_throw",
      attack_bonus: 0,
      save_dc: 13,
      save_ability: "dex",
      damage_dice: "2d4",
      damage_type: "force",
    });
    useSpellAttackProfile.mockReturnValue({ mutateAsync: attackProfileMutate, isPending: false });

    render(
      <SpellListByCircle
        characterId="char-1"
        campaignId="camp-1"
        spells={[leveledEntry]}
        classes={characterClasses}
        spellSlots={[{ spell_level: 1, used: 0, max: 1 }]}
      />,
    );

    expect(screen.queryByRole("button", { name: "atacar" })).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "ver CD" }));

    expect(attackProfileMutate).toHaveBeenCalledWith({
      spellEntryId: "entry-magic-missile",
      castAtLevel: 1,
    });
    expect(await screen.findByRole("button", { name: "CD 13 (Destreza)" })).toBeInTheDocument();
  });

  it("shows no roll controls for a spell with no attack, save, or damage", () => {
    catalogSpellDetailsById["spell-fire-bolt"] = { action_type: "cast_only", damages: [] };

    render(
      <SpellListByCircle
        characterId="char-1"
        campaignId="camp-1"
        spells={[cantripEntry]}
        classes={characterClasses}
        spellSlots={[]}
      />,
    );

    expect(screen.queryByRole("button", { name: "atacar" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "ver CD" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "dano" })).not.toBeInTheDocument();
  });
});
