import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const useCombat = vi.fn();
vi.mock("@/hooks/use-combat", () => ({
  useCombat: () => useCombat(),
}));

import { DamageDialog } from "./damage-dialog";

const participant = {
  id: "p-1",
  encounter_id: "enc-1",
  character_id: "char-1",
  npc_id: null,
  monster_id: null,
  name: "Aria",
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

describe("DamageDialog", () => {
  const updateParticipant = vi.fn();

  beforeEach(() => {
    updateParticipant.mockReset();
    useCombat.mockReturnValue({ updateParticipant });
  });

  it("sends update_participant (via useCombat) with the damaged HP on a preset tap", () => {
    render(<DamageDialog participant={participant} />);

    fireEvent.click(screen.getByRole("button", { name: "-5" }));

    expect(updateParticipant).toHaveBeenCalledWith("p-1", { hitPointCurrent: 15 });
  });

  it("sends the healed HP on a heal preset tap, clamped at hit_point_max is not enforced client-side", () => {
    render(<DamageDialog participant={participant} />);

    fireEvent.click(screen.getByRole("button", { name: "+10" }));

    expect(updateParticipant).toHaveBeenCalledWith("p-1", { hitPointCurrent: 30 });
  });

  it("clamps damage at 0 instead of going negative", () => {
    render(<DamageDialog participant={{ ...participant, hit_point_current: 3 }} />);

    fireEvent.click(screen.getByRole("button", { name: "-10" }));

    expect(updateParticipant).toHaveBeenCalledWith("p-1", { hitPointCurrent: 0 });
  });

  it("applies a custom amount as damage in two taps (type + confirm)", () => {
    render(<DamageDialog participant={participant} />);

    fireEvent.change(screen.getByLabelText(/quantidade de dano ou cura/i), {
      target: { value: "7" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Dano" }));

    expect(updateParticipant).toHaveBeenCalledWith("p-1", { hitPointCurrent: 13 });
  });

  it("ignores a non-numeric or non-positive custom amount", () => {
    render(<DamageDialog participant={participant} />);

    fireEvent.click(screen.getByRole("button", { name: "Cura" }));

    expect(updateParticipant).not.toHaveBeenCalled();
  });
});
