import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

const useUpdateCharacterInfo = vi.fn();
vi.mock("@/hooks/use-character", () => ({
  useUpdateCharacterInfo: () => useUpdateCharacterInfo(),
}));

import { CharacterInfoEditor } from "./character-info-editor";
import type { Character } from "@/types/character";

const baseCharacter: Character = {
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
  passive_perception: 10,
  passive_investigation: 10,
  passive_insight: 10,
  resources: [],
  ability_scores: [
    {
      id: "as-str",
      ability: "str",
      base_score: 10,
      asi_bonus: 0,
      misc_bonus: 0,
      modifier: 0,
      save_proficient: false,
      save_bonus: 0,
    },
    {
      id: "as-dex",
      ability: "dex",
      base_score: 14,
      asi_bonus: 0,
      misc_bonus: 0,
      modifier: 2,
      save_proficient: false,
      save_bonus: 2,
    },
  ],
  skills: [],
  classes: [],
  spells: [],
  spell_slots: [],
  equipment: [],
  features: [],
  feature_choices: [],
};

function openEditor() {
  fireEvent.click(screen.getByRole("button", { name: "Editar informações" }));
}

describe("CharacterInfoEditor", () => {
  it("edits name/alignment/background and submits without confirmation", async () => {
    const mutateAsync = vi.fn().mockResolvedValue(baseCharacter);
    useUpdateCharacterInfo.mockReturnValue({ mutateAsync, isPending: false });

    render(<CharacterInfoEditor character={baseCharacter} />);
    openEditor();

    fireEvent.change(screen.getByLabelText("Nome"), { target: { value: "Ariana" } });
    fireEvent.change(screen.getByLabelText("Alinhamento"), {
      target: { value: "Leal e Boa" },
    });
    fireEvent.change(screen.getByLabelText("Antecedente"), {
      target: { value: "Órfã" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Salvar" }));

    expect(screen.queryByRole("alertdialog")).not.toBeInTheDocument();
    await waitFor(() =>
      expect(mutateAsync).toHaveBeenCalledWith({
        name: "Ariana",
        alignment: "Leal e Boa",
        background: "Órfã",
      }),
    );
  });

  it("shows a confirmation dialog before submitting an ability score change", async () => {
    const mutateAsync = vi.fn().mockResolvedValue(baseCharacter);
    useUpdateCharacterInfo.mockReturnValue({ mutateAsync, isPending: false });

    render(<CharacterInfoEditor character={baseCharacter} />);
    openEditor();

    fireEvent.change(screen.getByLabelText("Força"), { target: { value: "12" } });
    fireEvent.click(screen.getByRole("button", { name: "Salvar" }));

    expect(screen.getByRole("alertdialog")).toBeInTheDocument();
    expect(mutateAsync).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole("button", { name: "Confirmar" }));

    await waitFor(() =>
      expect(mutateAsync).toHaveBeenCalledWith({
        ability_scores: [{ ability: "str", base_score: 12 }],
      }),
    );
  });

  it("cancelling the confirmation dialog does not submit", () => {
    const mutateAsync = vi.fn();
    useUpdateCharacterInfo.mockReturnValue({ mutateAsync, isPending: false });

    render(<CharacterInfoEditor character={baseCharacter} />);
    openEditor();

    fireEvent.change(screen.getByLabelText("Destreza"), { target: { value: "16" } });
    fireEvent.click(screen.getByRole("button", { name: "Salvar" }));

    const dialog = screen.getByRole("alertdialog");
    fireEvent.click(within(dialog).getByRole("button", { name: "Cancelar" }));

    expect(screen.queryByRole("alertdialog")).not.toBeInTheDocument();
    expect(mutateAsync).not.toHaveBeenCalled();
  });
});
