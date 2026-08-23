import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const useCatalogList = vi.fn();
const useCatalogEntry = vi.fn();
vi.mock("@/hooks/use-catalog", () => ({
  useCatalogList: (...args: unknown[]) => useCatalogList(...args),
  useCatalogEntry: (...args: unknown[]) => useCatalogEntry(...args),
}));

const useCombat = vi.fn();
vi.mock("@/hooks/use-combat", () => ({
  useCombat: () => useCombat(),
}));

import { MonsterPicker } from "./monster-picker";

const goblinSummary = { id: "monster-1", name: "Goblin", challenge_rating: 0.25 };
const goblinDetail = {
  id: "monster-1",
  name: "Goblin",
  hit_points: 7,
  armor_classes: [{ id: "ac-1", ac_type: "armor", value: 15, condition_id: null, description: null }],
};

describe("MonsterPicker", () => {
  const addParticipant = vi.fn();

  beforeEach(() => {
    addParticipant.mockReset();
    useCombat.mockReturnValue({ addParticipant });
    useCatalogList.mockReturnValue({ data: [goblinSummary] });
    useCatalogEntry.mockReturnValue({ data: undefined });
  });

  it("autocompletes name/HP/AC when a monster is selected from the catalog", () => {
    const { rerender } = render(<MonsterPicker campaignId="camp-1" />);

    fireEvent.change(screen.getByLabelText(/buscar monstro/i), {
      target: { value: "gob" },
    });
    fireEvent.click(screen.getByRole("button", { name: /goblin/i }));

    // Selecting triggers useCatalogEntry("monsters", "monster-1"); simulate
    // its data resolving by re-rendering with the mock now returning it.
    useCatalogEntry.mockReturnValue({ data: goblinDetail });
    rerender(<MonsterPicker campaignId="camp-1" />);

    expect(screen.getByLabelText(/^nome$/i)).toHaveValue("Goblin");
    expect(screen.getByLabelText(/pv máximo/i)).toHaveValue(7);
    expect(screen.getByLabelText(/^ca$/i)).toHaveValue(15);
  });

  it("submits the manually-entered fields (no catalog selection) as a new participant", () => {
    render(<MonsterPicker campaignId="camp-1" />);

    fireEvent.change(screen.getByLabelText(/^nome$/i), {
      target: { value: "Bandido" },
    });
    fireEvent.change(screen.getByLabelText(/pv máximo/i), { target: { value: "11" } });
    fireEvent.change(screen.getByLabelText(/^ca$/i), { target: { value: "12" } });
    fireEvent.change(screen.getByLabelText(/iniciativa/i), { target: { value: "8" } });
    fireEvent.change(screen.getByLabelText(/ordem de turno/i), { target: { value: "2" } });

    fireEvent.click(screen.getByRole("button", { name: /adicionar participante/i }));

    expect(addParticipant).toHaveBeenCalledWith({
      npc_id: null,
      character_id: null,
      name: "Bandido",
      hit_point_max: 11,
      armor_class: 12,
      initiative: 8,
      turn_order: 2,
    });
  });
});
