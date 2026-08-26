import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

const useAddCharacterFeature = vi.fn();
vi.mock("@/hooks/use-character", () => ({
  useAddCharacterFeature: () => useAddCharacterFeature(),
}));

const useCatalogFeature = vi.fn();
vi.mock("@/hooks/use-catalog", () => ({
  useCatalogFeature: (...args: unknown[]) => useCatalogFeature(...args),
}));

import { FeaturesSection } from "./character-sheet";

describe("FeaturesSection", () => {
  it("resolves and renders a picked level-up choice by name", () => {
    useAddCharacterFeature.mockReturnValue({ mutateAsync: vi.fn(), isPending: false });
    useCatalogFeature.mockReturnValue({
      data: { id: "dueling", feature_name: "Fighting Style: Dueling" },
    });

    render(
      <FeaturesSection
        characterId="char-1"
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

    render(<FeaturesSection characterId="char-1" features={[]} featureChoices={[]} />);

    expect(screen.getByText("Nenhuma característica registrada.")).toBeInTheDocument();
  });
});
