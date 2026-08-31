import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

const useUploadCharacterPortrait = vi.fn();
const useRemoveCharacterPortrait = vi.fn();
vi.mock("@/hooks/use-character", () => ({
  useUploadCharacterPortrait: () => useUploadCharacterPortrait(),
  useRemoveCharacterPortrait: () => useRemoveCharacterPortrait(),
}));

import { CharacterPortrait } from "./character-portrait";
import type { Character } from "@/types/character";

const baseCharacter: Character = {
  id: "char-1",
  campaign_member_id: "mem-1",
  name: "Aria Windrunner",
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
  concentration_remaining: { mode: null, remaining_rounds: null, remaining_seconds: null, expired: false },
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

describe("CharacterPortrait", () => {
  it("shows an initials placeholder when the character has no portrait", () => {
    useUploadCharacterPortrait.mockReturnValue({ mutateAsync: vi.fn(), isPending: false });
    useRemoveCharacterPortrait.mockReturnValue({ mutateAsync: vi.fn(), isPending: false });

    render(<CharacterPortrait character={baseCharacter} />);

    expect(screen.getByRole("img", { name: /sem imagem/i })).toHaveTextContent("AW");
    expect(screen.getByText("Adicionar imagem")).toBeInTheDocument();
    expect(screen.queryByText("Remover imagem")).not.toBeInTheDocument();
  });

  it("shows the uploaded image and a remove control when a portrait is set", () => {
    useUploadCharacterPortrait.mockReturnValue({ mutateAsync: vi.fn(), isPending: false });
    useRemoveCharacterPortrait.mockReturnValue({ mutateAsync: vi.fn(), isPending: false });

    render(
      <CharacterPortrait
        character={{ ...baseCharacter, portrait_url: "https://example.com/portrait.png" }}
      />,
    );

    const img = screen.getByRole("img", { name: /retrato de aria windrunner/i });
    expect(img).toHaveAttribute("src", "https://example.com/portrait.png");
    expect(screen.getByText("Trocar imagem")).toBeInTheDocument();
    expect(screen.getByText("Remover imagem")).toBeInTheDocument();
  });

  it("uploads a file and reflects the new portrait after the mutation resolves", async () => {
    const mutateAsync = vi.fn().mockResolvedValue({
      ...baseCharacter,
      portrait_url: "https://example.com/new.png",
    });
    useUploadCharacterPortrait.mockReturnValue({ mutateAsync, isPending: false });
    useRemoveCharacterPortrait.mockReturnValue({ mutateAsync: vi.fn(), isPending: false });

    render(<CharacterPortrait character={baseCharacter} />);

    const file = new File(["fake-image"], "portrait.png", { type: "image/png" });
    const input = screen.getByLabelText("Imagem do personagem");
    fireEvent.change(input, { target: { files: [file] } });

    await waitFor(() => expect(mutateAsync).toHaveBeenCalledWith(file));
  });

  it("removes the portrait via the remove control", async () => {
    const mutateAsync = vi.fn().mockResolvedValue({ ...baseCharacter, portrait_url: null });
    useUploadCharacterPortrait.mockReturnValue({ mutateAsync: vi.fn(), isPending: false });
    useRemoveCharacterPortrait.mockReturnValue({ mutateAsync, isPending: false });

    render(
      <CharacterPortrait
        character={{ ...baseCharacter, portrait_url: "https://example.com/portrait.png" }}
      />,
    );

    fireEvent.click(screen.getByText("Remover imagem"));

    await waitFor(() => expect(mutateAsync).toHaveBeenCalled());
  });

  it("shows an error message when the upload fails", async () => {
    const mutateAsync = vi.fn().mockRejectedValue(new Error("boom"));
    useUploadCharacterPortrait.mockReturnValue({ mutateAsync, isPending: false });
    useRemoveCharacterPortrait.mockReturnValue({ mutateAsync: vi.fn(), isPending: false });

    render(<CharacterPortrait character={baseCharacter} />);

    const file = new File(["fake-image"], "portrait.png", { type: "image/png" });
    const input = screen.getByLabelText("Imagem do personagem");
    fireEvent.change(input, { target: { files: [file] } });

    await waitFor(() => expect(screen.getByRole("alert")).toBeInTheDocument());
  });
});
