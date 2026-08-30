import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "@/lib/api/client";

const useCharacterSessions = vi.fn();
const reorderMutate = vi.fn();
vi.mock("@/hooks/use-character", () => ({
  useCharacterSessions: (...args: unknown[]) => useCharacterSessions(...args),
  useReorderCharacterSessions: () => ({ mutate: reorderMutate, isPending: false }),
}));

import { CharacterSessionsDropdown } from "./character-sessions-dropdown";

describe("CharacterSessionsDropdown", () => {
  const sessions = [
    {
      id: "session-1",
      campaign_id: "campaign-1",
      session_number: 1,
      title: "A Fuga de Phandalin",
      scheduled_date: null,
      status: "completed" as const,
      dm_notes: null,
      summary: null,
      created_at: "2026-01-01T00:00:00Z",
    },
    {
      id: "session-2",
      campaign_id: "campaign-1",
      session_number: 2,
      title: "O Covil do Dragão",
      scheduled_date: null,
      status: "in_progress" as const,
      dm_notes: null,
      summary: null,
      created_at: "2026-01-08T00:00:00Z",
    },
  ];

  beforeEach(() => {
    useCharacterSessions.mockReset();
    reorderMutate.mockReset();
  });

  it("is closed by default", () => {
    useCharacterSessions.mockReturnValue({ data: sessions, isLoading: false });
    render(<CharacterSessionsDropdown campaignId="campaign-1" characterId="char-1" />);

    expect(screen.queryByRole("menu")).not.toBeInTheDocument();
  });

  it("lists the character's sessions when opened", () => {
    useCharacterSessions.mockReturnValue({ data: sessions, isLoading: false });
    render(<CharacterSessionsDropdown campaignId="campaign-1" characterId="char-1" />);

    fireEvent.click(screen.getByRole("button", { name: /sessões/i }));

    expect(screen.getByRole("menu")).toBeInTheDocument();
    expect(screen.getByText(/A Fuga de Phandalin/)).toBeInTheDocument();
    expect(screen.getByText(/O Covil do Dragão/)).toBeInTheDocument();
  });

  it("links each session to its detail page under the current campaign", () => {
    useCharacterSessions.mockReturnValue({ data: sessions, isLoading: false });
    render(<CharacterSessionsDropdown campaignId="campaign-1" characterId="char-1" />);

    fireEvent.click(screen.getByRole("button", { name: /sessões/i }));

    const link = screen.getByText(/A Fuga de Phandalin/).closest("a");
    expect(link).toHaveAttribute("href", "/campaigns/campaign-1/sessions/session-1");
  });

  it("shows an empty state when the character hasn't appeared in any session", () => {
    useCharacterSessions.mockReturnValue({ data: [], isLoading: false });
    render(<CharacterSessionsDropdown campaignId="campaign-1" characterId="char-1" />);

    fireEvent.click(screen.getByRole("button", { name: /sessões/i }));

    expect(screen.getByText(/ainda não participou/i)).toBeInTheDocument();
  });

  it("closes when a session link is clicked", () => {
    useCharacterSessions.mockReturnValue({ data: sessions, isLoading: false });
    render(<CharacterSessionsDropdown campaignId="campaign-1" characterId="char-1" />);

    fireEvent.click(screen.getByRole("button", { name: /sessões/i }));
    fireEvent.click(screen.getByText(/A Fuga de Phandalin/));

    expect(screen.queryByRole("menu")).not.toBeInTheDocument();
  });

  it("disables the up button on the first session and the down button on the last", () => {
    useCharacterSessions.mockReturnValue({ data: sessions, isLoading: false });
    render(<CharacterSessionsDropdown campaignId="campaign-1" characterId="char-1" />);

    fireEvent.click(screen.getByRole("button", { name: /sessões/i }));

    expect(screen.getByRole("button", { name: /mover sessão a fuga de phandalin para cima/i })).toBeDisabled();
    expect(
      screen.getByRole("button", { name: /mover sessão o covil do dragão para baixo/i }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: /mover sessão a fuga de phandalin para baixo/i }),
    ).toBeEnabled();
    expect(
      screen.getByRole("button", { name: /mover sessão o covil do dragão para cima/i }),
    ).toBeEnabled();
  });

  it("moves a session down and saves the new order without touching the link's destination", () => {
    useCharacterSessions.mockReturnValue({ data: sessions, isLoading: false });
    render(<CharacterSessionsDropdown campaignId="campaign-1" characterId="char-1" />);

    fireEvent.click(screen.getByRole("button", { name: /sessões/i }));
    fireEvent.click(
      screen.getByRole("button", { name: /mover sessão a fuga de phandalin para baixo/i }),
    );

    expect(reorderMutate).toHaveBeenCalledTimes(1);
    expect(reorderMutate).toHaveBeenCalledWith(
      ["session-2", "session-1"],
      expect.objectContaining({ onError: expect.any(Function) }),
    );
    // The dropdown still stays open and the menu is untouched by the reorder click.
    expect(screen.getByRole("menu")).toBeInTheDocument();
  });

  it("moves a session up by swapping it with its predecessor", () => {
    useCharacterSessions.mockReturnValue({ data: sessions, isLoading: false });
    render(<CharacterSessionsDropdown campaignId="campaign-1" characterId="char-1" />);

    fireEvent.click(screen.getByRole("button", { name: /sessões/i }));
    fireEvent.click(
      screen.getByRole("button", { name: /mover sessão o covil do dragão para cima/i }),
    );

    expect(reorderMutate).toHaveBeenCalledWith(
      ["session-2", "session-1"],
      expect.objectContaining({ onError: expect.any(Function) }),
    );
  });

  it("shows an inline error when saving the order fails (e.g. a non-owner viewer)", () => {
    useCharacterSessions.mockReturnValue({ data: sessions, isLoading: false });
    reorderMutate.mockImplementation((_ids, options) => {
      options.onError(new ApiError(403, "Only the character's owner can do this"));
    });
    render(<CharacterSessionsDropdown campaignId="campaign-1" characterId="char-1" />);

    fireEvent.click(screen.getByRole("button", { name: /sessões/i }));
    fireEvent.click(
      screen.getByRole("button", { name: /mover sessão a fuga de phandalin para baixo/i }),
    );

    expect(screen.getByRole("alert")).toHaveTextContent(/only the character's owner/i);
  });
});
