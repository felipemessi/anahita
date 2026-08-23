import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const push = vi.fn();
vi.mock("next/navigation", () => ({
  useParams: () => ({ campaignId: "camp-1" }),
  useRouter: () => ({ push }),
}));

const useMyMembership = vi.fn();
vi.mock("@/hooks/use-campaign", () => ({
  useMyMembership: (...args: unknown[]) => useMyMembership(...args),
}));

const useCatalogList = vi.fn();
const useCatalogEntry = vi.fn();
vi.mock("@/hooks/use-catalog", () => ({
  useCatalogList: (...args: unknown[]) => useCatalogList(...args),
  useCatalogEntry: (...args: unknown[]) => useCatalogEntry(...args),
}));

const mutateAsync = vi.fn();
const useCreateCharacter = vi.fn();
vi.mock("@/hooks/use-character", () => ({
  useCreateCharacter: (...args: unknown[]) => useCreateCharacter(...args),
}));

import CharacterCreationWizardPage from "./page";

describe("CharacterCreationWizardPage", () => {
  beforeEach(() => {
    push.mockClear();
    mutateAsync.mockReset();
    mutateAsync.mockResolvedValue({ id: "char-1" });

    useMyMembership.mockReturnValue({
      data: { id: "mem-1", campaign_id: "camp-1", user_id: "user-1", role: "player", joined_at: "2026-01-01T00:00:00Z" },
    });
    useCreateCharacter.mockReturnValue({ mutateAsync, isPending: false });

    useCatalogList.mockImplementation((category: string) => {
      if (category === "races") return { data: [{ id: "race-1", name: "Elf", is_custom: false }] };
      if (category === "classes") return { data: [{ id: "class-1", name: "Fighter", is_custom: false }] };
      if (category === "backgrounds") return { data: [{ id: "bg-1", name: "Acolyte", is_custom: false }] };
      return { data: [] };
    });

    useCatalogEntry.mockImplementation((category: string, id: string) => {
      if (category === "races" && id === "race-1") {
        return { data: { id: "race-1", name: "Elf", subraces: [] } };
      }
      if (category === "classes" && id === "class-1") {
        return { data: { id: "class-1", name: "Fighter", subclasses: [] } };
      }
      if (category === "backgrounds" && id === "bg-1") {
        return { data: { id: "bg-1", name: "Acolyte", equipment: [] } };
      }
      return { data: undefined };
    });
  });

  it("walks through every step and submits the correct POST /characters payload", async () => {
    render(<CharacterCreationWizardPage />);

    // Step 1: race
    fireEvent.change(screen.getByLabelText(/escolha a raça/i), {
      target: { value: "race-1" },
    });
    fireEvent.click(screen.getByRole("button", { name: /próximo/i }));

    // Step 2: class
    fireEvent.change(screen.getByLabelText(/escolha a classe/i), {
      target: { value: "class-1" },
    });
    fireEvent.click(screen.getByRole("button", { name: /próximo/i }));

    // Step 3: background
    fireEvent.change(screen.getByLabelText(/nome do personagem/i), {
      target: { value: "Aria" },
    });
    fireEvent.change(screen.getByLabelText(/^antecedente$/i), {
      target: { value: "bg-1" },
    });
    fireEvent.change(screen.getByLabelText(/alinhamento/i), {
      target: { value: "Neutro e Bom" },
    });
    fireEvent.click(screen.getByRole("button", { name: /próximo/i }));

    // Step 4: ability scores — assign the standard array in order
    fireEvent.change(screen.getByLabelText(/força/i), { target: { value: "15" } });
    fireEvent.change(screen.getByLabelText(/destreza/i), { target: { value: "14" } });
    fireEvent.change(screen.getByLabelText(/constituição/i), { target: { value: "13" } });
    fireEvent.change(screen.getByLabelText(/inteligência/i), { target: { value: "12" } });
    fireEvent.change(screen.getByLabelText(/sabedoria/i), { target: { value: "10" } });
    fireEvent.change(screen.getByLabelText(/carisma/i), { target: { value: "8" } });
    fireEvent.click(screen.getByRole("button", { name: /próximo/i }));

    // Step 5: equipment (informational only)
    fireEvent.click(screen.getByRole("button", { name: /próximo/i }));

    // Step 6: review + submit
    fireEvent.click(screen.getByRole("button", { name: /criar personagem/i }));

    expect(mutateAsync).toHaveBeenCalledWith({
      campaign_member_id: "mem-1",
      name: "Aria",
      race_id: "race-1",
      subrace_id: null,
      alignment: "Neutro e Bom",
      background: "Acolyte",
      ability_scores: [
        { ability: "str", base_score: 15 },
        { ability: "dex", base_score: 14 },
        { ability: "con", base_score: 13 },
        { ability: "int", base_score: 12 },
        { ability: "wis", base_score: 10 },
        { ability: "cha", base_score: 8 },
      ],
      classes: [{ class_definition_id: "class-1", subclass_id: null, level: 1 }],
    });
  });
});
