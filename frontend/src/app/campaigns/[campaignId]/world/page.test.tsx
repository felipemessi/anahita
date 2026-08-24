import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("next/navigation", () => ({
  useParams: () => ({ campaignId: "campaign-1" }),
}));

const useNpcs = vi.fn();
const useLocations = vi.fn();
const useFactions = vi.fn();
const useWorldSearch = vi.fn();
vi.mock("@/hooks/use-world", () => ({
  useNpcs: (...args: unknown[]) => useNpcs(...args),
  useLocations: (...args: unknown[]) => useLocations(...args),
  useFactions: (...args: unknown[]) => useFactions(...args),
  useWorldSearch: (...args: unknown[]) => useWorldSearch(...args),
}));

import WorldHubPage from "./page";

describe("WorldHubPage", () => {
  beforeEach(() => {
    useNpcs.mockReturnValue({ data: [] });
    useLocations.mockReturnValue({ data: [] });
    useFactions.mockReturnValue({ data: [] });
    useWorldSearch.mockReturnValue({ data: undefined, isFetching: false });
  });

  it("shows the three section cards when there is no search query", () => {
    render(<WorldHubPage />);

    expect(screen.getByText("NPCs")).toBeInTheDocument();
    expect(screen.getByText("Locais")).toBeInTheDocument();
    expect(screen.getByText("Facções")).toBeInTheDocument();
  });

  it("shows search results combining NPCs, locations, factions, and wiki pages", () => {
    useWorldSearch.mockReturnValue({
      data: [
        { entity_type: "npc", id: "npc-1", name: "Volo", snippet: "A wandering..." },
        {
          entity_type: "location",
          id: "loc-1",
          name: "Waterdeep",
          snippet: "A misty city",
        },
        {
          entity_type: "faction",
          id: "fac-1",
          name: "Harpers",
          snippet: "Secret network",
        },
        {
          entity_type: "wiki_page",
          id: "wiki-1",
          name: "The Sunken Temple",
          snippet: "Deep beneath the lake...",
        },
      ],
      isFetching: false,
    });

    render(<WorldHubPage />);
    fireEvent.change(screen.getByLabelText(/buscar no world/i), {
      target: { value: "Water" },
    });

    expect(screen.getByText("Volo")).toBeInTheDocument();
    expect(screen.getByText("Waterdeep")).toBeInTheDocument();
    expect(screen.getByText("Harpers")).toBeInTheDocument();
    expect(screen.getByText("The Sunken Temple")).toBeInTheDocument();
    expect(screen.getByText("NPC")).toBeInTheDocument();
    expect(screen.getByText("Local")).toBeInTheDocument();
    expect(screen.getByText("Facção")).toBeInTheDocument();
    expect(screen.getByText("Wiki")).toBeInTheDocument();

    const wikiLink = screen.getByText("The Sunken Temple").closest("a");
    expect(wikiLink).toHaveAttribute(
      "href",
      "/campaigns/campaign-1/wiki/wiki-1",
    );
  });
});
