import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const useCharacters = vi.fn();
vi.mock("@/hooks/use-character", () => ({
  useCharacters: (...args: unknown[]) => useCharacters(...args),
}));

const useCombat = vi.fn();
vi.mock("@/hooks/use-combat", () => ({
  useCombat: () => useCombat(),
}));

import { CharacterPicker } from "./character-picker";

const aria = {
  id: "char-1",
  campaign_member_id: "member-1",
  name: "Aria",
  race_id: "race-1",
  subrace_id: null,
  level: 3,
  hit_point_max: 24,
  hit_point_current: 24,
  armor_class: 15,
};

describe("CharacterPicker", () => {
  const addParticipant = vi.fn();

  beforeEach(() => {
    addParticipant.mockReset();
    useCombat.mockReturnValue({ addParticipant });
    useCharacters.mockReturnValue({ data: [aria] });
  });

  it("autocompletes name/HP/AC when a character is selected", () => {
    render(<CharacterPicker campaignId="camp-1" />);

    fireEvent.change(screen.getByLabelText(/selecionar personagem/i), {
      target: { value: "char-1" },
    });

    expect(screen.getByLabelText(/^nome$/i)).toHaveValue("Aria");
    expect(screen.getByLabelText(/pv máximo/i)).toHaveValue(24);
    expect(screen.getByLabelText(/^ca$/i)).toHaveValue(15);
  });

  it("submits the selected character with character_id filled in", () => {
    render(<CharacterPicker campaignId="camp-1" />);

    fireEvent.change(screen.getByLabelText(/selecionar personagem/i), {
      target: { value: "char-1" },
    });
    fireEvent.change(screen.getByLabelText(/iniciativa/i), { target: { value: "14" } });
    fireEvent.change(screen.getByLabelText(/ordem de turno/i), { target: { value: "1" } });

    fireEvent.click(screen.getByRole("button", { name: /adicionar participante/i }));

    expect(addParticipant).toHaveBeenCalledWith({
      npc_id: null,
      character_id: "char-1",
      name: "Aria",
      hit_point_max: 24,
      armor_class: 15,
      initiative: 14,
      turn_order: 1,
    });
  });

  it("disables submit until a character is selected", () => {
    render(<CharacterPicker campaignId="camp-1" />);

    expect(screen.getByRole("button", { name: /adicionar participante/i })).toBeDisabled();
  });
});
