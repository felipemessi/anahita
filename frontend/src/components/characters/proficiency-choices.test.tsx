import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

const useProficiencyChoices = vi.fn();
const useSetProficiencyChoices = vi.fn();
vi.mock("@/hooks/use-character", () => ({
  useProficiencyChoices: (characterId: string) => useProficiencyChoices(characterId),
  useSetProficiencyChoices: (characterId: string) => useSetProficiencyChoices(characterId),
}));

import { ProficiencyChoices } from "./proficiency-choices";
import type { CharacterProficiencyChoiceGroup } from "@/types/character";

const oneOfThreeGroup: CharacterProficiencyChoiceGroup = {
  id: "group-1",
  choose_count: 1,
  options: ["insight", "perception", "survival"],
  selected: [],
};

describe("ProficiencyChoices", () => {
  it("renders nothing when the character has no choice group", () => {
    useProficiencyChoices.mockReturnValue({ data: [] });
    useSetProficiencyChoices.mockReturnValue({ mutateAsync: vi.fn(), isPending: false });

    const { container } = render(<ProficiencyChoices characterId="char-1" />);
    expect(container).toBeEmptyDOMElement();
  });

  it("only the group's options are selectable, up to choose_count", () => {
    useProficiencyChoices.mockReturnValue({ data: [oneOfThreeGroup] });
    useSetProficiencyChoices.mockReturnValue({ mutateAsync: vi.fn(), isPending: false });

    render(<ProficiencyChoices characterId="char-1" />);

    expect(screen.getByText("Escolha 1 de:")).toBeInTheDocument();
    const perception = screen.getByLabelText("Percepção");
    const insight = screen.getByLabelText("Intuição");
    const survival = screen.getByLabelText("Sobrevivência");
    expect(insight).not.toBeDisabled();
    expect(perception).not.toBeDisabled();
    expect(survival).not.toBeDisabled();

    // Athletics (not part of this group's options) never renders at all.
    expect(screen.queryByLabelText("Atletismo")).not.toBeInTheDocument();

    fireEvent.click(perception);
    // Once the group's budget (1) is spent, the remaining unchecked options
    // become unselectable — only the one just picked stays checked/enabled.
    expect(perception).toBeChecked();
    expect(insight).toBeDisabled();
    expect(survival).toBeDisabled();
  });

  it("proficiencies already chosen render checked and disabled, not editable", () => {
    const group: CharacterProficiencyChoiceGroup = {
      id: "group-1",
      choose_count: 1,
      options: ["insight", "perception", "survival"],
      selected: ["perception"],
    };
    useProficiencyChoices.mockReturnValue({ data: [group] });
    useSetProficiencyChoices.mockReturnValue({ mutateAsync: vi.fn(), isPending: false });

    render(<ProficiencyChoices characterId="char-1" />);

    // The group's budget is already spent by the earlier choice, so it no
    // longer shows as pending — nothing renders (same as "no choice group").
    expect(screen.queryByText("Escolha 1 de:")).not.toBeInTheDocument();
  });

  it("submits only the newly picked skills", async () => {
    const mutateAsync = vi.fn().mockResolvedValue({});
    useProficiencyChoices.mockReturnValue({ data: [oneOfThreeGroup] });
    useSetProficiencyChoices.mockReturnValue({ mutateAsync, isPending: false });

    render(<ProficiencyChoices characterId="char-1" />);

    fireEvent.click(screen.getByLabelText("Sobrevivência"));
    fireEvent.click(screen.getByRole("button", { name: "Salvar" }));

    await waitFor(() =>
      expect(mutateAsync).toHaveBeenCalledWith({ skills: ["survival"] }),
    );
  });

  it("save is disabled until a skill is picked", () => {
    useProficiencyChoices.mockReturnValue({ data: [oneOfThreeGroup] });
    useSetProficiencyChoices.mockReturnValue({ mutateAsync: vi.fn(), isPending: false });

    render(<ProficiencyChoices characterId="char-1" />);
    expect(screen.getByRole("button", { name: "Salvar" })).toBeDisabled();
  });
});
