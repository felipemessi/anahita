import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

// Stub out every subcomponent — this test only cares about the "PV atual"
// input staying in sync with `character.hit_point_current` across
// re-renders (a regression: it used to be captured once at mount via
// `useState` and never updated again).
vi.mock("@/components/catalog/catalog-filter-bar", () => ({ CatalogFilterBar: () => null }));
vi.mock("@/components/characters/ability-scores", () => ({ AbilityScores: () => null }));
vi.mock("@/components/characters/class-resources", () => ({ ClassResources: () => null }));
vi.mock("@/components/characters/character-info-editor", () => ({
  CharacterInfoEditor: () => null,
}));
vi.mock("@/components/characters/character-portrait", () => ({
  CharacterPortrait: () => null,
}));
vi.mock("@/components/characters/concentration-indicator", () => ({
  ConcentrationIndicator: () => null,
}));
vi.mock("@/components/characters/currency-tracker", () => ({ CurrencyTracker: () => null }));
vi.mock("@/components/characters/death-save-tracker", () => ({ DeathSaveTracker: () => null }));
vi.mock("@/components/characters/equipment-list", () => ({ EquipmentList: () => null }));
vi.mock("@/components/characters/hit-dice-tracker", () => ({ HitDiceTracker: () => null }));
vi.mock("@/components/characters/level-up-dialog", () => ({ LevelUpDialog: () => null }));
vi.mock("@/components/characters/passive-scores", () => ({ PassiveScores: () => null }));
vi.mock("@/components/characters/proficiency-choices", () => ({
  ProficiencyChoices: () => null,
}));
vi.mock("@/components/characters/skill-list", () => ({ SkillList: () => null }));
vi.mock("@/components/characters/spell-list-by-circle", () => ({ SpellListByCircle: () => null }));
vi.mock("@/components/characters/spell-slots", () => ({ SpellSlots: () => null }));

const useCatalogFeature = vi.fn();
const useCatalogList = vi.fn();
vi.mock("@/hooks/use-catalog", () => ({
  useCatalogFeature: (...args: unknown[]) => useCatalogFeature(...args),
  useCatalogList: (...args: unknown[]) => useCatalogList(...args),
}));

const useAddCharacterFeature = vi.fn();
const useRestCharacter = vi.fn();
const useUpdateCharacterHp = vi.fn();
vi.mock("@/hooks/use-character", () => ({
  useAddCharacterFeature: () => useAddCharacterFeature(),
  useRestCharacter: () => useRestCharacter(),
  useUpdateCharacterHp: () => useUpdateCharacterHp(),
}));

import { CharacterSheet } from "./character-sheet";

const baseCharacter = {
  id: "char-1",
  campaign_member_id: "mem-1",
  name: "Aria",
  race_id: "race-1",
  subrace_id: null,
  level: 1,
  experience_points: 0,
  alignment: null,
  background: null,
  hit_point_max: 20,
  hit_point_current: 12,
  temporary_hit_points: 0,
  armor_class: 14,
  speed: 30,
  inspiration: false,
  proficiency_bonus: 2,
  currency_cp: 0,
  death_save_successes: 0,
  death_save_failures: 0,
  is_dead: false,
  concentrating_spell_id: null,
  portrait_url: null,
  passive_perception: 10,
  passive_investigation: 10,
  passive_insight: 10,
  resources: [],
  ability_scores: [],
  skills: [],
  classes: [],
  spells: [],
  spell_slots: [],
  equipment: [],
  features: [],
  feature_choices: [],
};

describe("CharacterSheet", () => {
  beforeEach(() => {
    useCatalogFeature.mockReturnValue({ data: undefined });
    useCatalogList.mockReturnValue({ data: [] });
    useAddCharacterFeature.mockReturnValue({ mutateAsync: vi.fn(), isPending: false });
    useRestCharacter.mockReturnValue({ mutateAsync: vi.fn(), isPending: false });
    useUpdateCharacterHp.mockReturnValue({ mutateAsync: vi.fn(), isPending: false });
  });

  it("shows the character's current hit points on first render", () => {
    render(<CharacterSheet campaignId="camp-1" character={baseCharacter} />);

    expect(screen.getByLabelText("PV atual")).toHaveValue(12);
  });

  it("updates the 'PV atual' input when hit_point_current changes externally (e.g. a rest)", () => {
    const { rerender } = render(
      <CharacterSheet campaignId="camp-1" character={baseCharacter} />,
    );
    expect(screen.getByLabelText("PV atual")).toHaveValue(12);

    rerender(
      <CharacterSheet
        campaignId="camp-1"
        character={{ ...baseCharacter, hit_point_current: 20 }}
      />,
    );

    expect(screen.getByLabelText("PV atual")).toHaveValue(20);
  });
});
