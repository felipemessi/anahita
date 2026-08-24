import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("next/navigation", () => ({
  useParams: () => ({ campaignId: "campaign-1" }),
}));

const useWikiPages = vi.fn();
const useMyMembership = vi.fn();
vi.mock("@/hooks/use-wiki", () => ({
  useWikiPages: (...args: unknown[]) => useWikiPages(...args),
  useCreateWikiPage: () => ({ mutate: vi.fn(), isPending: false, isError: false }),
}));
vi.mock("@/hooks/use-campaign", () => ({
  useMyMembership: (...args: unknown[]) => useMyMembership(...args),
}));

import WikiPage from "./page";

describe("WikiPage (list)", () => {
  beforeEach(() => {
    useWikiPages.mockReturnValue({
      isLoading: false,
      data: [{ id: "page-1", title: "The Sunken Temple", slug: "the-sunken-temple", tags: null }],
    });
  });

  it("shows the create-page form only to the DM", () => {
    useMyMembership.mockReturnValue({ data: { role: "player" } });
    render(<WikiPage />);
    expect(screen.queryByPlaceholderText("Título")).not.toBeInTheDocument();
    expect(screen.getByText("The Sunken Temple")).toBeInTheDocument();
  });

  it("shows the create-page form to the DM", () => {
    useMyMembership.mockReturnValue({ data: { role: "dm" } });
    render(<WikiPage />);
    expect(screen.getByPlaceholderText("Título")).toBeInTheDocument();
  });
});
