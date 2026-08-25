import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const useCatalogList = vi.fn();
const useCatalogEntry = vi.fn();
vi.mock("@/hooks/use-catalog", () => ({
  useCatalogList: (...args: unknown[]) => useCatalogList(...args),
  useCatalogEntry: (...args: unknown[]) => useCatalogEntry(...args),
}));

const useLevelUpCharacter = vi.fn();
vi.mock("@/hooks/use-character", () => ({
  useLevelUpCharacter: () => useLevelUpCharacter(),
}));

import { ApiError } from "@/lib/api/client";

import { LevelUpDialog } from "./level-up-dialog";

const fighterClass = {
  id: "cc-1",
  class_definition_id: "fighter-id",
  subclass_id: null,
  level: 3,
  hit_dice_used: 0,
};

function classDetail(levels: Array<{ level: number; ability_score_bonuses: number | null }>) {
  return {
    id: "fighter-id",
    index: "fighter",
    name: "Fighter",
    hit_die: 10,
    primary_ability: "str",
    saving_throw_proficiencies: "Strength, Constitution",
    is_custom: false,
    levels,
    subclasses: [],
  };
}

describe("LevelUpDialog", () => {
  const mutateAsync = vi.fn();

  beforeEach(() => {
    mutateAsync.mockReset();
    useLevelUpCharacter.mockReturnValue({ mutateAsync, isPending: false });
    useCatalogList.mockImplementation((category: string) => {
      if (category === "classes") return { data: [{ id: "fighter-id", name: "Fighter" }] };
      if (category === "feats") return { data: [{ id: "feat-grappler", name: "Grappler" }] };
      return { data: [] };
    });
    useCatalogEntry.mockReturnValue({
      data: classDetail([{ level: 4, ability_score_bonuses: null }]),
    });
  });

  it("a non-ASI level submits with no ability/feat payload", async () => {
    mutateAsync.mockResolvedValue({ hit_point_max: 30 });
    render(
      <LevelUpDialog characterId="char-1" campaignId="camp-1" classes={[fighterClass]} />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Subir de nível" }));
    fireEvent.click(screen.getByRole("button", { name: "Confirmar" }));

    await waitFor(() =>
      expect(mutateAsync).toHaveBeenCalledWith({
        class_definition_id: "fighter-id",
        ability_score_increases: undefined,
        feat_id: undefined,
      }),
    );
    expect(await screen.findByText(/agora está no nível 4/)).toBeInTheDocument();
  });

  it("an ASI level defaults to +2 in one ability", async () => {
    useCatalogEntry.mockReturnValue({
      data: classDetail([{ level: 4, ability_score_bonuses: 2 }]),
    });
    mutateAsync.mockResolvedValue({ hit_point_max: 30 });
    render(
      <LevelUpDialog characterId="char-1" campaignId="camp-1" classes={[fighterClass]} />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Subir de nível" }));
    fireEvent.click(screen.getByRole("button", { name: "Confirmar" }));

    await waitFor(() =>
      expect(mutateAsync).toHaveBeenCalledWith({
        class_definition_id: "fighter-id",
        ability_score_increases: { str: 2 },
        feat_id: undefined,
      }),
    );
  });

  it("choosing a feat at an ASI level submits feat_id instead", async () => {
    useCatalogEntry.mockReturnValue({
      data: classDetail([{ level: 4, ability_score_bonuses: 2 }]),
    });
    mutateAsync.mockResolvedValue({ hit_point_max: 30 });
    render(
      <LevelUpDialog characterId="char-1" campaignId="camp-1" classes={[fighterClass]} />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Subir de nível" }));
    fireEvent.change(screen.getByLabelText("Tipo de melhoria"), {
      target: { value: "feat" },
    });
    fireEvent.change(screen.getByLabelText("Talento"), {
      target: { value: "feat-grappler" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Confirmar" }));

    await waitFor(() =>
      expect(mutateAsync).toHaveBeenCalledWith({
        class_definition_id: "fighter-id",
        ability_score_increases: undefined,
        feat_id: "feat-grappler",
      }),
    );
  });

  it("shows the backend's error on failure", async () => {
    mutateAsync.mockRejectedValue(new ApiError(422, "This class is already at level 20"));
    render(
      <LevelUpDialog characterId="char-1" campaignId="camp-1" classes={[fighterClass]} />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Subir de nível" }));
    fireEvent.click(screen.getByRole("button", { name: "Confirmar" }));

    expect(await screen.findByText(/already at level 20/i)).toBeInTheDocument();
  });
});
