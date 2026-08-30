import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const useCreateCustomEntry = vi.fn();
const useLanguages = vi.fn();
const useProficiencies = vi.fn();
const useAddRaceAbilityBonus = vi.fn();
const useAddRaceTrait = vi.fn();
const useAddRaceSubrace = vi.fn();
const useCatalogEntry = vi.fn();

vi.mock("@/hooks/use-catalog", () => ({
  useCreateCustomEntry: (...args: unknown[]) => useCreateCustomEntry(...args),
  useLanguages: (...args: unknown[]) => useLanguages(...args),
  useProficiencies: (...args: unknown[]) => useProficiencies(...args),
  useAddRaceAbilityBonus: (...args: unknown[]) => useAddRaceAbilityBonus(...args),
  useAddRaceTrait: (...args: unknown[]) => useAddRaceTrait(...args),
  useAddRaceSubrace: (...args: unknown[]) => useAddRaceSubrace(...args),
  useCatalogEntry: (...args: unknown[]) => useCatalogEntry(...args),
}));

import { RaceHomebrewForm } from "./race-homebrew-form";

const LANGUAGES = [
  { id: "lang-common", index: "common", language_type: "standard", is_custom: false },
  { id: "lang-elvish", index: "elvish", language_type: "standard", is_custom: false },
];

const PROFICIENCIES = [
  {
    id: "prof-perception",
    index: "skill-perception",
    proficiency_type: "skill",
    skill_id: "skill-1",
    ability_score_id: null,
    equipment_category_id: null,
    is_custom: false,
  },
];

const CREATED_RACE = {
  id: "race-1",
  index: null,
  name: "Duskling",
  description: "A twilight-born folk.",
  age: "Matures at 18.",
  alignment_desc: "Usually neutral.",
  size_description: "Medium, about 5-6 ft tall.",
  language_desc: "One language of your choice.",
  speed: 35,
  size: "medium",
  darkvision_range: 60,
  is_custom: true,
  traits: [],
  subraces: [],
  ability_bonuses: [],
  languages: [],
  proficiencies: [],
};

describe("RaceHomebrewForm", () => {
  const mutateAsync = vi.fn();
  const addBonusMutateAsync = vi.fn();
  const addTraitMutateAsync = vi.fn();
  const addSubraceMutateAsync = vi.fn();

  beforeEach(() => {
    mutateAsync.mockReset();
    mutateAsync.mockResolvedValue(CREATED_RACE);
    useCreateCustomEntry.mockReset();
    useCreateCustomEntry.mockReturnValue({ mutateAsync, isPending: false });

    useLanguages.mockReset();
    useLanguages.mockReturnValue({ data: LANGUAGES });
    useProficiencies.mockReset();
    useProficiencies.mockReturnValue({ data: PROFICIENCIES });

    addBonusMutateAsync.mockReset().mockResolvedValue({});
    useAddRaceAbilityBonus.mockReset();
    useAddRaceAbilityBonus.mockReturnValue({
      mutateAsync: addBonusMutateAsync,
      isPending: false,
    });

    addTraitMutateAsync.mockReset().mockResolvedValue({});
    useAddRaceTrait.mockReset();
    useAddRaceTrait.mockReturnValue({ mutateAsync: addTraitMutateAsync, isPending: false });

    addSubraceMutateAsync.mockReset().mockResolvedValue({});
    useAddRaceSubrace.mockReset();
    useAddRaceSubrace.mockReturnValue({
      mutateAsync: addSubraceMutateAsync,
      isPending: false,
    });

    useCatalogEntry.mockReset();
    useCatalogEntry.mockReturnValue({ data: undefined });
  });

  it("renders the race-only fields (speed, size, darkvision) absent from the generic form", () => {
    render(<RaceHomebrewForm campaignId="camp-1" />);
    expect(screen.getByLabelText(/deslocamento/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^tamanho$/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/visão no escuro/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/idade/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/alinhamento/i)).toBeInTheDocument();
  });

  it("lists languages/proficiencies as checkboxes fetched from the catalog", () => {
    render(<RaceHomebrewForm campaignId="camp-1" />);
    expect(screen.getByLabelText("common")).toBeInTheDocument();
    expect(screen.getByLabelText("elvish")).toBeInTheDocument();
    expect(screen.getByLabelText("skill-perception")).toBeInTheDocument();
  });

  it("submits every customized attribute, including checked language/proficiency ids", async () => {
    render(<RaceHomebrewForm campaignId="camp-1" />);

    fireEvent.change(screen.getByLabelText(/^nome$/i), { target: { value: "Duskling" } });
    fireEvent.change(screen.getByLabelText(/deslocamento/i), { target: { value: "35" } });
    fireEvent.change(screen.getByLabelText(/^tamanho$/i), { target: { value: "small" } });
    fireEvent.change(screen.getByLabelText(/visão no escuro/i), { target: { value: "60" } });
    fireEvent.change(screen.getByLabelText(/idade/i), { target: { value: "Matures at 18." } });
    fireEvent.change(screen.getByLabelText(/alinhamento/i), {
      target: { value: "Usually neutral." },
    });
    fireEvent.change(screen.getByLabelText(/tamanho \(descrição\)/i), {
      target: { value: "Medium, about 5-6 ft tall." },
    });
    fireEvent.change(screen.getByLabelText(/idiomas \(texto livre\)/i), {
      target: { value: "One language of your choice." },
    });
    fireEvent.click(screen.getByLabelText("common"));
    fireEvent.click(screen.getByLabelText("skill-perception"));

    fireEvent.click(screen.getByRole("button", { name: /criar raça homebrew/i }));

    await screen.findByText(/criada\. adicione/i);
    expect(mutateAsync).toHaveBeenCalledWith(
      expect.objectContaining({
        name: "Duskling",
        speed: 35,
        size: "small",
        darkvision_range: 60,
        age: "Matures at 18.",
        alignment_desc: "Usually neutral.",
        size_description: "Medium, about 5-6 ft tall.",
        language_desc: "One language of your choice.",
        language_ids: ["lang-common"],
        proficiency_ids: ["prof-perception"],
      }),
    );
  });

  it("shows the attach panel after creation and lets the DM add an ability bonus", async () => {
    render(<RaceHomebrewForm campaignId="camp-1" />);
    fireEvent.change(screen.getByLabelText(/^nome$/i), { target: { value: "Duskling" } });
    fireEvent.click(screen.getByRole("button", { name: /criar raça homebrew/i }));

    await screen.findByText(/criada\. adicione/i);

    const bonusInput = document.getElementById("race-bonus-value") as HTMLInputElement;
    fireEvent.change(bonusInput, { target: { value: "2" } });
    fireEvent.click(screen.getByRole("button", { name: /adicionar bônus/i }));

    await screen.findByRole("button", { name: /adicionar bônus/i });
    expect(addBonusMutateAsync).toHaveBeenCalledWith({ ability: "str", bonus: 2 });
  });
});
