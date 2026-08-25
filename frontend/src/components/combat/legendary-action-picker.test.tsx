import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const useCatalogEntry = vi.fn();
vi.mock("@/hooks/use-catalog", () => ({
  useCatalogEntry: (...args: unknown[]) => useCatalogEntry(...args),
}));

const useCombat = vi.fn();
vi.mock("@/hooks/use-combat", () => ({
  useCombat: () => useCombat(),
}));

const useNpcs = vi.fn();
vi.mock("@/hooks/use-world", () => ({
  useNpcs: (...args: unknown[]) => useNpcs(...args),
}));

import { LegendaryActionPicker } from "./legendary-action-picker";

const dragon = {
  id: "p-1",
  encounter_id: "enc-1",
  character_id: null,
  npc_id: null,
  monster_id: "monster-dragon",
  name: "Dragão",
  initiative: 20,
  hit_point_max: 200,
  hit_point_current: 200,
  temporary_hit_points: 0,
  armor_class: 19,
  turn_order: 1,
  is_active: true,
  conditions: [],
  effects: [],
  concentration_dc: null,
  legendary_actions_used: 0,
  reactions_used: 0,
};

const fighter = { ...dragon, id: "p-2", name: "Aldric", monster_id: null, character_id: "char-1" };

const dragonStatBlock = {
  id: "monster-dragon",
  legendary_actions: [{ id: "la-1", name: "Tail Attack" }],
  reactions: [{ id: "re-1", name: "Parry" }],
};

describe("LegendaryActionPicker", () => {
  const sendLegendaryAction = vi.fn();
  const triggerReaction = vi.fn();

  beforeEach(() => {
    sendLegendaryAction.mockReset();
    triggerReaction.mockReset();
    useCombat.mockReturnValue({ sendLegendaryAction, triggerReaction });
    useNpcs.mockReturnValue({ data: [] });
    useCatalogEntry.mockReturnValue({ data: dragonStatBlock });
  });

  it("renders nothing for a participant with no stat block", () => {
    useCatalogEntry.mockReturnValue({ data: undefined });
    const { container } = render(
      <LegendaryActionPicker
        campaignId="camp-1"
        participant={fighter}
        otherParticipants={[dragon]}
      />,
    );

    expect(container).toBeEmptyDOMElement();
  });

  it("using a legendary action sends the picked action and target", () => {
    render(
      <LegendaryActionPicker
        campaignId="camp-1"
        participant={dragon}
        otherParticipants={[fighter]}
      />,
    );

    fireEvent.change(screen.getByLabelText("Ação lendária"), {
      target: { value: "la-1" },
    });
    fireEvent.click(screen.getByRole("button", { name: /usar/i }));

    expect(sendLegendaryAction).toHaveBeenCalledWith("p-1", "p-2", "la-1");
  });

  it("disables the legendary action button once the round budget is spent", () => {
    render(
      <LegendaryActionPicker
        campaignId="camp-1"
        participant={{ ...dragon, legendary_actions_used: 3 }}
        otherParticipants={[fighter]}
      />,
    );

    expect(screen.getByRole("button", { name: /usar/i })).toBeDisabled();
  });

  it("triggering a reaction sends the picked reaction and target", () => {
    render(
      <LegendaryActionPicker
        campaignId="camp-1"
        participant={dragon}
        otherParticipants={[fighter]}
      />,
    );

    fireEvent.change(screen.getByLabelText("Reação"), { target: { value: "re-1" } });
    fireEvent.click(screen.getByRole("button", { name: /disparar/i }));

    expect(triggerReaction).toHaveBeenCalledWith("p-1", "p-2", "re-1");
  });

  it("disables the reaction button once used this round", () => {
    render(
      <LegendaryActionPicker
        campaignId="camp-1"
        participant={{ ...dragon, reactions_used: 1 }}
        otherParticipants={[fighter]}
      />,
    );

    expect(screen.getByRole("button", { name: /disparar/i })).toBeDisabled();
  });
});
