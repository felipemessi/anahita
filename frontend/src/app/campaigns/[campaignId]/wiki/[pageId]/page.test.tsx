import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("next/navigation", () => ({
  useParams: () => ({ campaignId: "campaign-1", pageId: "page-1" }),
  useRouter: () => ({ push: vi.fn() }),
}));

const useWikiPage = vi.fn();
const useMyMembership = vi.fn();
vi.mock("@/hooks/use-wiki", () => ({
  useWikiPage: (...args: unknown[]) => useWikiPage(...args),
  useUpdateWikiPage: () => ({ mutate: vi.fn(), isPending: false, isError: false }),
  useDeleteWikiPage: () => ({ mutate: vi.fn(), isPending: false }),
  useCreateWikiPageLink: () => ({ mutate: vi.fn(), isPending: false, isError: false }),
  useDeleteWikiPageLink: () => ({ mutate: vi.fn(), isPending: false }),
}));
vi.mock("@/hooks/use-campaign", () => ({
  useMyMembership: (...args: unknown[]) => useMyMembership(...args),
}));
vi.mock("@/hooks/use-world", () => ({
  useNpcs: () => ({ data: [{ id: "npc-1", name: "Temple Guardian" }] }),
  useLocations: () => ({ data: [] }),
  useFactions: () => ({ data: [] }),
}));

import WikiPageDetailPage from "./page";

describe("WikiPageDetailPage", () => {
  beforeEach(() => {
    useWikiPage.mockReturnValue({
      isLoading: false,
      data: {
        id: "page-1",
        campaign_id: "campaign-1",
        title: "The Sunken Temple",
        slug: "the-sunken-temple",
        content: "**Deep** beneath the lake.",
        tags: "dungeon, lake",
        created_by_id: "user-1",
        created_at: "2026-08-24T00:00:00Z",
        links: [{ id: "link-1", wiki_page_id: "page-1", npc_id: "npc-1", location_id: null, faction_id: null }],
      },
    });
  });

  it("renders the markdown content and linked NPC for a player, without edit controls", () => {
    useMyMembership.mockReturnValue({ data: { role: "player" } });

    render(<WikiPageDetailPage />);

    expect(screen.getByText("The Sunken Temple")).toBeInTheDocument();
    expect(screen.getByText("Deep")).toBeInTheDocument();
    expect(screen.getByText("NPC: Temple Guardian")).toBeInTheDocument();
    expect(screen.queryByText("Editar")).not.toBeInTheDocument();
    expect(screen.queryByText("Apagar")).not.toBeInTheDocument();
  });

  it("shows edit/delete controls to the DM", () => {
    useMyMembership.mockReturnValue({ data: { role: "dm" } });

    render(<WikiPageDetailPage />);

    expect(screen.getByText("Editar")).toBeInTheDocument();
    expect(screen.getByText("Apagar")).toBeInTheDocument();
  });
});
