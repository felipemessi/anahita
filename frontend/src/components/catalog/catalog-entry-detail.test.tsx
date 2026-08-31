import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const push = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push }),
}));

const useMyMembership = vi.fn();
vi.mock("@/hooks/use-campaign", () => ({
  useMyMembership: (...args: unknown[]) => useMyMembership(...args),
}));

const deleteMutate = vi.fn();
const useDeleteCustomEntry = vi.fn();
vi.mock("@/hooks/use-catalog", () => ({
  useDeleteCustomEntry: (...args: unknown[]) => useDeleteCustomEntry(...args),
}));

import { ApiError } from "@/lib/api/client";
import type { Background, ClassDefinition, Feat, Item, MagicItem, Monster, Race, Rule, Spell } from "@/types/catalog";

import { CatalogEntryDetail } from "./catalog-entry-detail";

const RACE: Race = {
  id: "race-1",
  index: "elf",
  name: "Elf",
  description: "A graceful folk.",
  age: "Matures at 18.",
  alignment_desc: "Usually good.",
  size_description: "Medium.",
  language_desc: "Common and Elvish.",
  speed: 30,
  size: "medium",
  darkvision_range: 60,
  is_custom: false,
  traits: [
    { id: "trait-1", trait_name: "Keen Senses", description: "Proficiency in Perception.", mechanical_effect: null },
  ],
  subraces: [],
  ability_bonuses: [{ id: "ab-1", ability: "dex", bonus: 2 }],
  languages: [],
  proficiencies: [],
};

const CLASS_DEFINITION: ClassDefinition = {
  id: "class-1",
  index: "wizard",
  name: "Wizard",
  hit_die: 6,
  primary_ability: "int",
  saving_throw_proficiencies: "int, wis",
  is_custom: false,
  levels: [
    {
      id: "level-1",
      level: 1,
      proficiency_bonus: 2,
      ability_score_bonuses: null,
      features: [
        {
          id: "feat-1",
          index: null,
          level: 1,
          feature_name: "Spellcasting",
          description: "Cast wizard spells.",
          mechanical_effect: null,
          parent_feature_id: null,
          prerequisites: [],
        },
      ],
      spell_slots: [{ id: "slot-1", spell_level: 1, slot_count: 2 }],
      resources: [],
    },
  ],
  subclasses: [],
};

const SPELL: Spell = {
  id: "spell-1",
  index: "fireball",
  name: "Fireball",
  level: 3,
  school: "evocation",
  casting_time: "1 action",
  range: "150 feet",
  duration: "Instantaneous",
  components: "V, S, M",
  ritual: false,
  concentration: false,
  action_type: "saving_throw",
  target_type: "area",
  save_ability_score_id: null,
  description: "A bright streak flashes.",
  higher_levels: "The damage increases by 1d6 for each slot level above 3rd.",
  is_custom: false,
  classes: [{ id: "cls-1", name: "Wizard" }],
  damages: [{ id: "dmg-1", damage_type: "fire", scaling_type: "slot_level", scaling_key: 3, dice_expression: "8d6" }],
};

const ITEM: Item = {
  id: "item-1",
  index: "longsword",
  name: "Longsword",
  item_type: "weapon",
  equipment_category: "Martial Melee",
  rarity: null,
  weight: 1.5,
  cost: 15,
  description: "A versatile blade.",
  is_custom: false,
  properties: [{ id: "prop-1", name: "Versatile" }],
  weapon_detail: { id: "wd-1", damage_dice: "1d8", damage_type: "slashing", weapon_range: "melee" },
  armor_detail: null,
};

const MAGIC_ITEM: MagicItem = {
  id: "magic-1",
  index: "bag-of-holding",
  name: "Bag of Holding",
  description: "Holds more than it should.",
  equipment_category: "Wondrous Item",
  rarity: "uncommon",
  is_custom: false,
  is_variant: false,
  variant_of_id: null,
  variants: [],
};

const BACKGROUND: Background = {
  id: "bg-1",
  index: "acolyte",
  name: "Acolyte",
  personality_traits: "Calm.",
  ideals: "Faith.",
  bonds: "My temple.",
  flaws: "Naive.",
  is_custom: false,
  proficiencies: [],
  equipment: [{ id: "eq-1", item_id: "item-x", item_name: "Holy symbol", quantity: 1 }],
  feature: { id: "feat-bg-1", feature_name: "Shelter of the Faithful", description: "Free healing." },
};

const FEAT: Feat = {
  id: "feat-1",
  index: "alert",
  name: "Alert",
  description: "Always ready for danger.",
  is_custom: false,
  prerequisites: [],
};

const RULE: Rule = {
  id: "rule-1",
  index: "combat",
  name: "Combat",
  desc: "Rules for combat.",
  is_custom: false,
  sections: [
    { id: "sec-1", index: "initiative", name: "Initiative", desc: "Roll a d20.", is_custom: false },
  ],
};

const MONSTER: Monster = {
  id: "monster-1",
  index: "goblin",
  name: "Goblin",
  description: "A small, cunning humanoid.",
  size: "small",
  creature_type: "humanoid",
  creature_subtype: null,
  alignment: "neutral evil",
  hit_points: 7,
  hit_dice: "2d6",
  challenge_rating: 0.25,
  xp: 50,
  proficiency_bonus: 2,
  languages: "Common, Goblin",
  strength: 8,
  dexterity: 14,
  constitution: 10,
  intelligence: 10,
  wisdom: 8,
  charisma: 8,
  is_custom: false,
  speed: null,
  senses: null,
  armor_classes: [],
  proficiencies: [],
  damage_modifiers: [],
  condition_immunities: [],
  actions: [],
  legendary_actions: [],
  reactions: [],
  special_abilities: [],
};

describe("CatalogEntryDetail", () => {
  beforeEach(() => {
    push.mockReset();
    deleteMutate.mockReset();
    useDeleteCustomEntry.mockReturnValue({ mutateAsync: deleteMutate });
    useMyMembership.mockReturnValue({ data: undefined });
  });

  it("renders the race detail component instead of a raw JSON dump", () => {
    render(<CatalogEntryDetail category="races" entry={RACE} campaignId="camp-1" />);
    expect(screen.getByText("Elf")).toBeInTheDocument();
    expect(screen.getByText(/keen senses/i)).toBeInTheDocument();
    expect(screen.queryByText("Detalhes técnicos")).not.toBeInTheDocument();
  });

  it("renders the class detail component", () => {
    render(<CatalogEntryDetail category="classes" entry={CLASS_DEFINITION} campaignId="camp-1" />);
    expect(screen.getByText(/bônus de proficiência \+2/i)).toBeInTheDocument();
    expect(screen.getByText(/spellcasting/i)).toBeInTheDocument();
  });

  it("renders the spell detail component", () => {
    render(<CatalogEntryDetail category="spells" entry={SPELL} campaignId="camp-1" />);
    expect(screen.getByText(/bright streak flashes/i)).toBeInTheDocument();
    expect(screen.getByText(/8d6/)).toBeInTheDocument();
  });

  it("renders the item detail component", () => {
    render(<CatalogEntryDetail category="equipment" entry={ITEM} campaignId="camp-1" />);
    expect(screen.getByText(/versatile blade/i)).toBeInTheDocument();
    expect(screen.getByText("1d8")).toBeInTheDocument();
  });

  it("renders the magic item detail component", () => {
    render(<CatalogEntryDetail category="magic-items" entry={MAGIC_ITEM} campaignId="camp-1" />);
    expect(screen.getByText(/holds more than it should/i)).toBeInTheDocument();
  });

  it("renders the background detail component", () => {
    render(<CatalogEntryDetail category="backgrounds" entry={BACKGROUND} campaignId="camp-1" />);
    expect(screen.getByText("Calm.")).toBeInTheDocument();
    expect(screen.getByText(/shelter of the faithful/i)).toBeInTheDocument();
  });

  it("renders the feat detail component", () => {
    render(<CatalogEntryDetail category="feats" entry={FEAT} campaignId="camp-1" />);
    expect(screen.getByText(/always ready for danger/i)).toBeInTheDocument();
  });

  it("renders the rule detail component", () => {
    render(<CatalogEntryDetail category="rules" entry={RULE} campaignId="camp-1" />);
    expect(screen.getByText("Initiative")).toBeInTheDocument();
  });

  it("still renders the monster stat block for monsters", () => {
    render(<CatalogEntryDetail category="monsters" entry={MONSTER} campaignId="camp-1" />);
    expect(screen.getAllByText("Goblin").length).toBeGreaterThan(0);
    expect(screen.getByText(/cunning humanoid/i)).toBeInTheDocument();
  });

  it("hides the delete button for a non-DM member", () => {
    useMyMembership.mockReturnValue({ data: { role: "player" } });
    render(<CatalogEntryDetail category="races" entry={{ ...RACE, is_custom: true }} campaignId="camp-1" />);
    expect(screen.queryByRole("button", { name: /excluir/i })).not.toBeInTheDocument();
  });

  it("hides the delete button for SRD content, even for the DM", () => {
    useMyMembership.mockReturnValue({ data: { role: "dm" } });
    render(<CatalogEntryDetail category="races" entry={{ ...RACE, is_custom: false }} campaignId="camp-1" />);
    expect(screen.queryByRole("button", { name: /excluir/i })).not.toBeInTheDocument();
  });

  it("shows the delete button for the DM on homebrew content and deletes on confirm", async () => {
    useMyMembership.mockReturnValue({ data: { role: "dm" } });
    deleteMutate.mockResolvedValue(undefined);
    render(<CatalogEntryDetail category="races" entry={{ ...RACE, is_custom: true }} campaignId="camp-1" />);

    fireEvent.click(screen.getByRole("button", { name: /excluir/i }));
    const dialog = screen.getByRole("alertdialog");
    expect(dialog).toBeInTheDocument();

    fireEvent.click(within(dialog).getByRole("button", { name: "Excluir" }));

    await waitFor(() => expect(deleteMutate).toHaveBeenCalledWith("race-1"));
    await waitFor(() => expect(push).toHaveBeenCalledWith("/campaigns/camp-1/catalog/races"));
  });

  it("shows the API error message in the confirm dialog area on a 409 conflict", async () => {
    useMyMembership.mockReturnValue({ data: { role: "dm" } });
    deleteMutate.mockRejectedValue(new ApiError(409, "Race is still referenced by a character"));
    render(<CatalogEntryDetail category="races" entry={{ ...RACE, is_custom: true }} campaignId="camp-1" />);

    fireEvent.click(screen.getByRole("button", { name: /excluir/i }));
    fireEvent.click(within(screen.getByRole("alertdialog")).getByRole("button", { name: "Excluir" }));

    await waitFor(() =>
      expect(screen.getByText(/race is still referenced by a character/i)).toBeInTheDocument(),
    );
    expect(push).not.toHaveBeenCalled();
  });
});
