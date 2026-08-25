import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const useCatalogList = vi.fn();
vi.mock("@/hooks/use-catalog", () => ({
  useCatalogList: (...args: unknown[]) => useCatalogList(...args),
}));

const useRestCharacter = vi.fn();
vi.mock("@/hooks/use-character", () => ({
  useRestCharacter: () => useRestCharacter(),
}));

import { ApiError } from "@/lib/api/client";

import { HitDiceTracker } from "./hit-dice-tracker";

const fighterClass = { id: "cc-1", class_definition_id: "fighter-id", subclass_id: null, level: 3, hit_dice_used: 1 };

describe("HitDiceTracker", () => {
  const mutateAsync = vi.fn();

  beforeEach(() => {
    mutateAsync.mockReset();
    mutateAsync.mockResolvedValue(undefined);
    useRestCharacter.mockReturnValue({ mutateAsync, isPending: false });
    useCatalogList.mockReturnValue({ data: [{ id: "fighter-id", name: "Fighter" }] });
  });

  it("shows dice available out of the class level", () => {
    render(
      <HitDiceTracker characterId="char-1" campaignId="camp-1" classes={[fighterClass]} />,
    );

    expect(screen.getByLabelText("2 de 3 dados de vida disponíveis")).toBeInTheDocument();
  });

  it("spending hit dice takes a short rest for the chosen class and count", async () => {
    render(
      <HitDiceTracker characterId="char-1" campaignId="camp-1" classes={[fighterClass]} />,
    );

    fireEvent.change(screen.getByLabelText("Quantidade de dados de vida a gastar de Fighter"), {
      target: { value: "2" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Gastar dado de vida" }));

    await waitFor(() =>
      expect(mutateAsync).toHaveBeenCalledWith({
        rest_type: "short",
        hit_dice_spent: [{ character_class_id: "cc-1", count: 2 }],
      }),
    );
  });

  it("disables spending when no dice are available", () => {
    render(
      <HitDiceTracker
        characterId="char-1"
        campaignId="camp-1"
        classes={[{ ...fighterClass, hit_dice_used: 3 }]}
      />,
    );

    expect(screen.getByRole("button", { name: "Gastar dado de vida" })).toBeDisabled();
  });

  it("shows the backend's error on failure", async () => {
    mutateAsync.mockRejectedValue(new ApiError(422, "Not enough hit dice available"));
    render(
      <HitDiceTracker characterId="char-1" campaignId="camp-1" classes={[fighterClass]} />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Gastar dado de vida" }));

    expect(await screen.findByText(/not enough hit dice/i)).toBeInTheDocument();
  });
});
