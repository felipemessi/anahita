import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const replace = vi.fn();
vi.mock("next/navigation", () => ({
  useParams: () => ({ campaignId: "camp-1" }),
  useRouter: () => ({ replace }),
}));

const useMyMembership = vi.fn();
vi.mock("@/hooks/use-campaign", () => ({
  useMyMembership: (...args: unknown[]) => useMyMembership(...args),
}));

const useCharacters = vi.fn();
vi.mock("@/hooks/use-character", () => ({
  useCharacters: (...args: unknown[]) => useCharacters(...args),
}));

const useCatalogList = vi.fn();
vi.mock("@/hooks/use-catalog", () => ({
  useCatalogList: (...args: unknown[]) => useCatalogList(...args),
}));

import CharactersPage from "./page";

const myMember = { id: "member-1", campaign_id: "camp-1", user_id: "u-1", role: "player" };
const dmMember = { id: "member-dm", campaign_id: "camp-1", user_id: "u-dm", role: "dm" };

const myFullCharacter = {
  id: "char-1",
  campaign_member_id: "member-1",
  name: "Aldric",
  race_id: "race-human",
  level: 3,
  hit_point_max: 30,
  hit_point_current: 25,
  classes: [{ id: "cc-1", class_definition_id: "class-fighter", subclass_id: null, level: 3 }],
};

const otherSummary = {
  id: "char-2",
  campaign_member_id: "member-2",
  name: "Brenna",
  race_id: "race-elf",
  level: 2,
  classes: [{ id: "cc-2", class_definition_id: "class-wizard", subclass_id: null, level: 2 }],
};

describe("CharactersPage", () => {
  beforeEach(() => {
    replace.mockReset();
    useCatalogList.mockImplementation((category: string) => {
      if (category === "races") {
        return {
          data: [
            { id: "race-human", name: "Human" },
            { id: "race-elf", name: "Elf" },
          ],
        };
      }
      if (category === "classes") {
        return {
          data: [
            { id: "class-fighter", name: "Fighter" },
            { id: "class-wizard", name: "Wizard" },
          ],
        };
      }
      return { data: [] };
    });
  });

  // These three use a second own-character alongside `otherSummary` so the
  // player has *two* own characters — the sole-own-character auto-redirect
  // (tested separately below) doesn't fire, and the list actually renders.
  const secondOwnCharacter = { ...myFullCharacter, id: "char-4", name: "Second" };

  it("a player sees a summary card (no link) for another player's character", () => {
    useMyMembership.mockReturnValue({ data: myMember });
    useCharacters.mockReturnValue({
      data: [myFullCharacter, secondOwnCharacter, otherSummary],
      isLoading: false,
    });

    render(<CharactersPage />);

    expect(screen.getByText("Brenna")).toBeInTheDocument();
    expect(screen.getByText(/Elf.*Wizard.*Nível 2/)).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /Brenna/ })).not.toBeInTheDocument();
  });

  it("a player still gets a link to their own character's full sheet", () => {
    useMyMembership.mockReturnValue({ data: myMember });
    useCharacters.mockReturnValue({
      data: [myFullCharacter, secondOwnCharacter, otherSummary],
      isLoading: false,
    });

    render(<CharactersPage />);

    const link = screen.getByRole("link", { name: /Aldric/ });
    expect(link).toHaveAttribute("href", "/campaigns/camp-1/characters/char-1");
  });

  it("the DM sees links to every character, including summaries", () => {
    useMyMembership.mockReturnValue({ data: dmMember });
    useCharacters.mockReturnValue({
      data: [myFullCharacter, otherSummary],
      isLoading: false,
    });

    render(<CharactersPage />);

    expect(screen.getByRole("link", { name: /Brenna/ })).toBeInTheDocument();
  });

  it("a player with exactly one character is redirected to its sheet", () => {
    useMyMembership.mockReturnValue({ data: myMember });
    useCharacters.mockReturnValue({ data: [myFullCharacter], isLoading: false });

    render(<CharactersPage />);

    expect(replace).toHaveBeenCalledWith("/campaigns/camp-1/characters/char-1");
  });

  it("the DM is never auto-redirected even with exactly one character visible", () => {
    useMyMembership.mockReturnValue({ data: dmMember });
    useCharacters.mockReturnValue({ data: [myFullCharacter], isLoading: false });

    render(<CharactersPage />);

    expect(replace).not.toHaveBeenCalled();
  });

  it("a player with more than one character sees the list, no redirect", () => {
    useMyMembership.mockReturnValue({ data: myMember });
    useCharacters.mockReturnValue({
      data: [myFullCharacter, { ...myFullCharacter, id: "char-3", name: "Second" }],
      isLoading: false,
    });

    render(<CharactersPage />);

    expect(replace).not.toHaveBeenCalled();
    expect(screen.getByText("Aldric")).toBeInTheDocument();
    expect(screen.getByText("Second")).toBeInTheDocument();
  });
});
