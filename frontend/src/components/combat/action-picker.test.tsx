import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const useCombat = vi.fn();
vi.mock("@/hooks/use-combat", () => ({
  useCombat: () => useCombat(),
}));

const useCharacter = vi.fn();
vi.mock("@/hooks/use-character", () => ({
  useCharacter: (...args: unknown[]) => useCharacter(...args),
}));

const useCatalogEntry = vi.fn();
const useCatalogList = vi.fn();
vi.mock("@/hooks/use-catalog", () => ({
  useCatalogEntry: (...args: unknown[]) => useCatalogEntry(...args),
  useCatalogList: (...args: unknown[]) => useCatalogList(...args),
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

  beforeEach(() => {
    declareAction.mockReset();
    useCombat.mockReturnValue({ declareAction });
    useCharacter.mockReturnValue({
      data: {
        equipment: [{ id: "eq-1", item_id: "item-longsword", equipped: true }],
        spells: [{ id: "sp-1", spell_id: "spell-fire-bolt" }],
      },
    });
    useCatalogEntry.mockReturnValue({ data: undefined });
    useCatalogList.mockImplementation((category: string) => {
      if (category === "equipment") return { data: [{ id: "item-longsword", name: "Longsword" }] };
      if (category === "spells") return { data: [{ id: "spell-fire-bolt", name: "Fire Bolt" }] };
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
});
