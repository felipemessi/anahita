import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const params = { campaignId: "camp-1", category: "races" };
vi.mock("next/navigation", () => ({
  useParams: () => params,
}));

const useCatalogList = vi.fn();
vi.mock("@/hooks/use-catalog", () => ({
  useCatalogList: (...args: unknown[]) => useCatalogList(...args),
}));

const useMyMembership = vi.fn();
vi.mock("@/hooks/use-campaign", () => ({
  useMyMembership: (...args: unknown[]) => useMyMembership(...args),
}));

import CatalogCategoryPage from "./page";

describe("CatalogCategoryPage", () => {
  beforeEach(() => {
    useMyMembership.mockReturnValue({ data: undefined });
  });

  it("re-queries the catalog with the typed search term", () => {
    useCatalogList.mockReturnValue({
      data: [{ id: "race-1", name: "Elf", is_custom: false }],
      isLoading: false,
    });

    render(<CatalogCategoryPage />);
    expect(screen.getByText("Elf")).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText(/buscar no catálogo/i), {
      target: { value: "dwarf" },
    });

    expect(useCatalogList).toHaveBeenLastCalledWith("races", {
      search: "dwarf",
      campaign_id: "camp-1",
    });
  });

  it("shows a message for an unknown category", () => {
    params.category = "bogus";
    render(<CatalogCategoryPage />);
    expect(screen.getByText(/categoria de catálogo desconhecida/i)).toBeInTheDocument();
    params.category = "races";
  });

  it("shows the 'Criar homebrew' button for the DM", () => {
    useCatalogList.mockReturnValue({ data: [], isLoading: false });
    useMyMembership.mockReturnValue({
      data: { id: "mem-1", campaign_id: "camp-1", user_id: "user-1", role: "dm", joined_at: "2026-01-01T00:00:00Z" },
    });

    render(<CatalogCategoryPage />);
    expect(screen.getByRole("link", { name: /criar homebrew/i })).toBeInTheDocument();
  });

  it("hides the 'Criar homebrew' button for a read-only player", () => {
    useCatalogList.mockReturnValue({ data: [], isLoading: false });
    useMyMembership.mockReturnValue({
      data: { id: "mem-1", campaign_id: "camp-1", user_id: "user-2", role: "player", joined_at: "2026-01-01T00:00:00Z" },
    });

    render(<CatalogCategoryPage />);
    expect(screen.queryByRole("link", { name: /criar homebrew/i })).not.toBeInTheDocument();
  });
});
