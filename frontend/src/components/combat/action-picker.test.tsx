import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { RollLogProvider } from "@/components/characters/roll-log";

const useCombat = vi.fn();
vi.mock("@/hooks/use-combat", () => ({
  useCombat: () => useCombat(),
}));

const useCharacter = vi.fn();
const useCastCharacterSpell = vi.fn();
vi.mock("@/hooks/use-character", () => ({
  useCharacter: (...args: unknown[]) => useCharacter(...args),
  useCastCharacterSpell: (...args: unknown[]) => useCastCharacterSpell(...args),
}));

const useCatalogEntry = vi.fn();
const useCatalogList = vi.fn();
const useAbilityScores = vi.fn();
vi.mock("@/hooks/use-catalog", () => ({
  useCatalogEntry: (...args: unknown[]) => useCatalogEntry(...args),
  useCatalogList: (...args: unknown[]) => useCatalogList(...args),
  useAbilityScores: (...args: unknown[]) => useAbilityScores(...args),
}));

import { ActionPicker } from "./action-picker";

const fighter = {
  id: "p-1",
  encounter_id: "enc-1",
  character_id: "char-1",
  npc_id: null,
  monster_id: null,
  name: "Aldric",
  initiative: 15,
  hit_point_max: 20,
  hit_point_current: 20,
  temporary_hit_points: 0,
  armor_class: 14,
  turn_order: 0,
  is_active: true,
  conditions: [],
  effects: [],
  concentration_dc: null,
  legendary_actions_used: 0,
  reactions_used: 0,
};

const goblin = { ...fighter, id: "p-2", name: "Goblin", character_id: null };

describe("ActionPicker", () => {
  const declareAction = vi.fn();
  const castSpellMutate = vi.fn();

  beforeEach(() => {
    declareAction.mockReset();
    castSpellMutate.mockReset();
    castSpellMutate.mockResolvedValue({ character: {}, save_dc: null, target_participant_id: null });
    useCombat.mockReturnValue({ declareAction });
    useCastCharacterSpell.mockReturnValue({ mutateAsync: castSpellMutate, isPending: false });
    useCharacter.mockReturnValue({
      data: {
        id: "char-1",
        equipment: [{ id: "eq-1", item_id: "item-longsword", equipped: true }],
        spells: [
          { id: "sp-1", spell_id: "spell-fire-bolt" },
          { id: "sp-2", spell_id: "spell-bless" },
          { id: "sp-3", spell_id: "spell-mage-armor" },
        ],
        ability_scores: [{ ability: "wis", save_bonus: 3 }],
      },
    });
    useAbilityScores.mockReturnValue({
      data: [
        { id: "ability-wis", index: "wis", is_custom: false },
        { id: "ability-str", index: "str", is_custom: false },
      ],
    });
    useCatalogEntry.mockImplementation((category: string, id: string) => {
      if (category === "spells" && id === "spell-bless") {
        return {
          data: {
            id: "spell-bless",
            name: "Bless",
            action_type: "saving_throw",
            target_type: "enemy",
            save_ability_score_id: "ability-wis",
          },
        };
      }
      if (category === "spells" && id === "spell-mage-armor") {
        return {
          data: {
            id: "spell-mage-armor",
            name: "Mage Armor",
            action_type: "cast_only",
            target_type: "self",
            save_ability_score_id: null,
          },
        };
      }
      if (category === "spells" && id === "spell-fire-bolt") {
        return {
          data: {
            id: "spell-fire-bolt",
            name: "Fire Bolt",
            action_type: "attack_roll",
            target_type: "enemy",
            save_ability_score_id: null,
          },
        };
      }
      return { data: undefined };
    });
    useCatalogList.mockImplementation((category: string) => {
      if (category === "equipment") return { data: [{ id: "item-longsword", name: "Longsword" }] };
      if (category === "spells") {
        return {
          data: [
            { id: "spell-fire-bolt", name: "Fire Bolt" },
            { id: "spell-bless", name: "Bless" },
            { id: "spell-mage-armor", name: "Mage Armor" },
          ],
        };
      }
      return { data: [] };
    });
  });

  it("declaring a weapon attack sends the equipped weapon and chosen target", () => {
    render(
      <ActionPicker campaignId="camp-1" participant={fighter} otherParticipants={[goblin]} />,
    );

    fireEvent.change(screen.getByLabelText("Alvo"), { target: { value: "p-2" } });
    fireEvent.change(screen.getByLabelText("Arma"), { target: { value: "eq-1" } });
    fireEvent.click(screen.getByRole("button", { name: "Declarar" }));

    expect(declareAction).toHaveBeenCalledWith({
      actionType: "attack_weapon",
      participant_id: "p-1",
      target_id: "p-2",
      weapon_equipment_id: "eq-1",
      monster_action_id: undefined,
    });
  });

  it("declaring grapple doesn't require weapon/spell fields", () => {
    render(
      <ActionPicker campaignId="camp-1" participant={fighter} otherParticipants={[goblin]} />,
    );

    fireEvent.change(screen.getByLabelText("Ação"), { target: { value: "grapple" } });
    fireEvent.change(screen.getByLabelText("Alvo"), { target: { value: "p-2" } });
    fireEvent.click(screen.getByRole("button", { name: "Declarar" }));

    expect(declareAction).toHaveBeenCalledWith({
      actionType: "grapple",
      participant_id: "p-1",
      target_id: "p-2",
    });
  });

  it("a flavor action (e.g. dash) declares against the actor itself, no target field", () => {
    render(
      <ActionPicker campaignId="camp-1" participant={fighter} otherParticipants={[goblin]} />,
    );

    fireEvent.change(screen.getByLabelText("Ação"), { target: { value: "dash" } });
    expect(screen.queryByLabelText("Alvo")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Declarar" }));

    expect(declareAction).toHaveBeenCalledWith({
      actionType: "dash",
      participant_id: "p-1",
      target_id: "p-1",
    });
  });

  it("declaring a manual attack sends the typed bonus and damage expression", () => {
    render(
      <ActionPicker campaignId="camp-1" participant={fighter} otherParticipants={[goblin]} />,
    );

    fireEvent.change(screen.getByLabelText("Ação"), {
      target: { value: "attack_weapon_manual" },
    });
    fireEvent.change(screen.getByLabelText("Alvo"), { target: { value: "p-2" } });
    fireEvent.change(screen.getByLabelText(/bônus de ataque/i), { target: { value: "5" } });
    fireEvent.change(screen.getByLabelText(/dano/i), { target: { value: "1d8+3" } });
    fireEvent.click(screen.getByRole("button", { name: "Declarar" }));

    expect(declareAction).toHaveBeenCalledWith({
      actionType: "attack_weapon",
      participant_id: "p-1",
      target_id: "p-2",
      manual_attack_bonus: 5,
      manual_damage_expression: "1d8+3",
    });
  });

  it("the manual roll fields stay hidden by default — automatic rolling is the default action", () => {
    render(
      <ActionPicker campaignId="camp-1" participant={fighter} otherParticipants={[goblin]} />,
    );

    expect(screen.queryByLabelText(/resultado do ataque/i)).not.toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Digitar rolagem manualmente" }),
    ).toBeInTheDocument();
  });

  it("typing a manual attack/damage roll overrides the server's roll", () => {
    render(
      <ActionPicker campaignId="camp-1" participant={fighter} otherParticipants={[goblin]} />,
    );

    fireEvent.change(screen.getByLabelText("Alvo"), { target: { value: "p-2" } });
    fireEvent.change(screen.getByLabelText("Arma"), { target: { value: "eq-1" } });
    fireEvent.click(screen.getByRole("button", { name: "Digitar rolagem manualmente" }));
    fireEvent.change(screen.getByLabelText(/resultado do ataque/i), {
      target: { value: "18" },
    });
    fireEvent.change(screen.getByLabelText(/resultado do dano/i), {
      target: { value: "9" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Declarar" }));

    expect(declareAction).toHaveBeenCalledWith({
      actionType: "attack_weapon",
      participant_id: "p-1",
      target_id: "p-2",
      weapon_equipment_id: "eq-1",
      monster_action_id: undefined,
      manual_attack_roll: 18,
      manual_damage_roll: 9,
    });
  });

  it("a manual contest roll sends manual_attack_roll/manual_target_roll for grapple", () => {
    render(
      <ActionPicker campaignId="camp-1" participant={fighter} otherParticipants={[goblin]} />,
    );

    fireEvent.change(screen.getByLabelText("Ação"), { target: { value: "grapple" } });
    fireEvent.change(screen.getByLabelText("Alvo"), { target: { value: "p-2" } });
    fireEvent.click(screen.getByRole("button", { name: "Digitar rolagem manualmente" }));
    fireEvent.change(screen.getByLabelText(/teste do atacante/i), {
      target: { value: "16" },
    });
    fireEvent.change(screen.getByLabelText(/teste do alvo/i), { target: { value: "10" } });
    fireEvent.click(screen.getByRole("button", { name: "Declarar" }));

    expect(declareAction).toHaveBeenCalledWith({
      actionType: "grapple",
      participant_id: "p-1",
      target_id: "p-2",
      manual_attack_roll: 16,
      manual_target_roll: 10,
    });
  });

  it("flavor actions (nothing to roll) don't offer a manual-roll toggle", () => {
    render(
      <ActionPicker campaignId="camp-1" participant={fighter} otherParticipants={[goblin]} />,
    );

    fireEvent.change(screen.getByLabelText("Ação"), { target: { value: "dash" } });

    expect(
      screen.queryByRole("button", { name: "Digitar rolagem manualmente" }),
    ).not.toBeInTheDocument();
  });

  describe("casting a non-attack spell (cast_spell_effect)", () => {
    function selectCastEffect() {
      render(
        <RollLogProvider>
          <ActionPicker campaignId="camp-1" participant={fighter} otherParticipants={[goblin]} />
        </RollLogProvider>,
      );
      fireEvent.change(screen.getByLabelText("Ação"), {
        target: { value: "cast_spell_effect" },
      });
    }

    it("a self-only cast_only spell needs no target and casts directly", async () => {
      selectCastEffect();

      fireEvent.change(screen.getByLabelText("Magia"), { target: { value: "sp-3" } });
      expect(screen.queryByLabelText("Alvo")).not.toBeInTheDocument();

      fireEvent.click(screen.getByRole("button", { name: "Declarar" }));

      expect(castSpellMutate).toHaveBeenCalledWith({
        spellEntryId: "sp-3",
        data: { target_participant_id: undefined },
      });
    });

    it("a saving_throw spell asks for a target before it can be declared", () => {
      selectCastEffect();

      fireEvent.change(screen.getByLabelText("Magia"), { target: { value: "sp-2" } });

      expect(screen.getByLabelText("Alvo")).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "Declarar" })).toBeDisabled();

      fireEvent.change(screen.getByLabelText("Alvo"), { target: { value: "p-2" } });
      expect(screen.getByRole("button", { name: "Declarar" })).toBeEnabled();
    });

    it("casting a saving_throw spell shows the DC and a roll shortcut for the target's save", async () => {
      castSpellMutate.mockResolvedValue({
        character: {},
        save_dc: 14,
        target_participant_id: "p-2",
      });
      selectCastEffect();

      fireEvent.change(screen.getByLabelText("Magia"), { target: { value: "sp-2" } });
      fireEvent.change(screen.getByLabelText("Alvo"), { target: { value: "p-2" } });
      fireEvent.click(screen.getByRole("button", { name: "Declarar" }));

      expect(castSpellMutate).toHaveBeenCalledWith({
        spellEntryId: "sp-2",
        data: { target_participant_id: "p-2" },
      });

      expect(await screen.findByText(/CD 14/)).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: "Rolar Resistência de Sabedoria (+3)" }),
      ).toBeInTheDocument();
    });

    it("picking an attack_roll spell here hints to use the attack flow instead", () => {
      selectCastEffect();

      fireEvent.change(screen.getByLabelText("Magia"), { target: { value: "sp-1" } });

      expect(screen.getByText(/use "conjurar magia \(ataque\)" em vez disso/i)).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "Declarar" })).toBeDisabled();
    });
  });
});
