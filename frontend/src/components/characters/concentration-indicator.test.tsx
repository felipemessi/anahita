import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const useCatalogEntry = vi.fn();
vi.mock("@/hooks/use-catalog", () => ({
  useCatalogEntry: (...args: unknown[]) => useCatalogEntry(...args),
}));

const useSetCharacterConcentration = vi.fn();
vi.mock("@/hooks/use-character", () => ({
  useSetCharacterConcentration: () => useSetCharacterConcentration(),
}));

import { ApiError } from "@/lib/api/client";

import { ConcentrationIndicator } from "./concentration-indicator";

describe("ConcentrationIndicator", () => {
  const mutateAsync = vi.fn();

  beforeEach(() => {
    mutateAsync.mockReset();
    mutateAsync.mockResolvedValue(undefined);
    useSetCharacterConcentration.mockReturnValue({ mutateAsync, isPending: false });
  });

  it("renders nothing when not concentrating", () => {
    useCatalogEntry.mockReturnValue({ data: undefined });
    const { container } = render(
      <ConcentrationIndicator characterId="char-1" concentratingSpellId={null} />,
    );

    expect(container).toBeEmptyDOMElement();
  });

  it("shows the concentrated spell's name", () => {
    useCatalogEntry.mockReturnValue({ data: { name: "Bless" } });
    render(
      <ConcentrationIndicator characterId="char-1" concentratingSpellId="spell-bless" />,
    );

    expect(screen.getByText("Bless")).toBeInTheDocument();
  });

  it("changes indicator when the concentrated spell changes", () => {
    useCatalogEntry.mockReturnValue({ data: { name: "Bless" } });
    const { rerender } = render(
      <ConcentrationIndicator characterId="char-1" concentratingSpellId="spell-bless" />,
    );
    expect(screen.getByText("Bless")).toBeInTheDocument();

    useCatalogEntry.mockReturnValue({ data: { name: "Hold Person" } });
    rerender(
      <ConcentrationIndicator characterId="char-1" concentratingSpellId="spell-hold-person" />,
    );

    expect(screen.getByText("Hold Person")).toBeInTheDocument();
    expect(screen.queryByText("Bless")).not.toBeInTheDocument();
  });

  it("ending concentration calls the endpoint with a null spell_id", async () => {
    useCatalogEntry.mockReturnValue({ data: { name: "Bless" } });
    render(
      <ConcentrationIndicator characterId="char-1" concentratingSpellId="spell-bless" />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Encerrar concentração" }));

    await waitFor(() => expect(mutateAsync).toHaveBeenCalledWith({ spell_id: null }));
  });

  it("shows the backend's error on failure", async () => {
    useCatalogEntry.mockReturnValue({ data: { name: "Bless" } });
    mutateAsync.mockRejectedValue(new ApiError(404, "Spell not known by this character"));
    render(
      <ConcentrationIndicator characterId="char-1" concentratingSpellId="spell-bless" />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Encerrar concentração" }));

    expect(await screen.findByText(/spell not known/i)).toBeInTheDocument();
  });
});
