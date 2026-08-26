import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

const useAddCharacterFeature = vi.fn();
vi.mock("@/hooks/use-character", () => ({
  useAddCharacterFeature: () => useAddCharacterFeature(),
}));

const useCatalogFeature = vi.fn();
const useCatalogList = vi.fn();
vi.mock("@/hooks/use-catalog", () => ({
  useCatalogFeature: (...args: unknown[]) => useCatalogFeature(...args),
  useCatalogList: (...args: unknown[]) => useCatalogList(...args),
}));

import { FeaturesSection } from "./character-sheet";

describe("FeaturesSection", () => {
  it("resolves and renders a picked level-up choice by name", () => {
    useAddCharacterFeature.mockReturnValue({ mutateAsync: vi.fn(), isPending: false });
    useCatalogFeature.mockReturnValue({
      data: { id: "dueling", feature_name: "Fighting Style: Dueling" },
    });
    useCatalogList.mockReturnValue({ data: [] });

    render(
      <FeaturesSection
        characterId="char-1"
        campaignId="camp-1"
        features={[]}
        featureChoices={[
          { id: "choice-1", feature_id: "fighting-style", feature_option_id: "dueling" },
        ]}
      />,
    );

    expect(screen.getByText("Fighting Style: Dueling")).toBeInTheDocument();
  });

  it("shows the empty state when there are no features or choices", () => {
    useAddCharacterFeature.mockReturnValue({ mutateAsync: vi.fn(), isPending: false });
    useCatalogFeature.mockReturnValue({ data: undefined });
    useCatalogList.mockReturnValue({ data: [] });

    render(
      <FeaturesSection
        characterId="char-1"
        campaignId="camp-1"
        features={[]}
        featureChoices={[]}
      />,
    );

    expect(screen.getByText("Nenhuma característica registrada.")).toBeInTheDocument();
  });

  it("adding a class feature uses free-text fields, not the feat catalog search", async () => {
    const mutateAsync = vi.fn().mockResolvedValue(undefined);
    useAddCharacterFeature.mockReturnValue({ mutateAsync, isPending: false });
    useCatalogFeature.mockReturnValue({ data: undefined });
    useCatalogList.mockReturnValue({ data: [{ id: "feat-1", name: "Alert", is_custom: false }] });

    render(
      <FeaturesSection
        characterId="char-1"
        campaignId="camp-1"
        features={[]}
        featureChoices={[]}
      />,
    );

    expect(screen.queryByPlaceholderText("Buscar por nome…")).not.toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Nome da fonte"), { target: { value: "Fighter" } });
    fireEvent.change(screen.getByLabelText("Característica"), {
      target: { value: "Second Wind" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Adicionar" }));

    await waitFor(() =>
      expect(mutateAsync).toHaveBeenCalledWith({
        source_type: "class",
        source_name: "Fighter",
        feature_name: "Second Wind",
        description: null,
      }),
    );
  });

  it("adding a feat searches the campaign's feat catalog and picks one", async () => {
    const mutateAsync = vi.fn().mockResolvedValue(undefined);
    useAddCharacterFeature.mockReturnValue({ mutateAsync, isPending: false });
    useCatalogFeature.mockReturnValue({ data: undefined });
    useCatalogList.mockReturnValue({
      data: [
        { id: "feat-1", name: "Alert", is_custom: false },
        { id: "feat-2", name: "Lucky", is_custom: false },
      ],
    });

    render(
      <FeaturesSection
        characterId="char-1"
        campaignId="camp-1"
        features={[]}
        featureChoices={[]}
      />,
    );

    fireEvent.change(screen.getByLabelText("Origem"), { target: { value: "feat" } });
    fireEvent.change(screen.getByPlaceholderText("Buscar por nome…"), {
      target: { value: "luck" },
    });

    expect(screen.queryByText("Alert")).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Lucky" }));

    expect(screen.getByText("Lucky")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Adicionar" }));

    await waitFor(() =>
      expect(mutateAsync).toHaveBeenCalledWith({
        source_type: "feat",
        source_name: "Talento",
        feature_name: "Lucky",
        description: null,
      }),
    );
  });
});
