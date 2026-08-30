import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const useCharacterSessions = vi.fn();
vi.mock("@/hooks/use-character", () => ({
  useCharacterSessions: (...args: unknown[]) => useCharacterSessions(...args),
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
});
