import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("next/navigation", () => ({
  useParams: () => ({ campaignId: "campaign-1" }),
}));

const useSessions = vi.fn();
vi.mock("@/hooks/use-session", () => ({
  useSessions: (...args: unknown[]) => useSessions(...args),
}));

import RecapPage from "./page";

function makeSession(overrides: Partial<Record<string, unknown>>) {
  return {
    id: "session-x",
    campaign_id: "campaign-1",
    session_number: 1,
    title: "Untitled",
    scheduled_date: null,
    status: "completed",
    dm_notes: null,
    summary: null,
    created_at: "2026-08-24T00:00:00Z",
    ...overrides,
  };
}

describe("RecapPage", () => {
  beforeEach(() => {
    useSessions.mockReset();
  });

  it("renders summaries in session-number order and skips sessions without one", () => {
    useSessions.mockReturnValue({
      isLoading: false,
      data: [
        makeSession({ id: "s2", session_number: 2, title: "Return", summary: "They came back." }),
        makeSession({ id: "s3", session_number: 3, title: "No Recap Yet", summary: null }),
        makeSession({ id: "s1", session_number: 1, title: "Beginning", summary: "It began." }),
      ],
    });

    render(<RecapPage />);

    const items = screen.getAllByRole("listitem");
    expect(items).toHaveLength(2);
    expect(items[0]).toHaveTextContent("Sessão 1 — Beginning");
    expect(items[0]).toHaveTextContent("It began.");
    expect(items[1]).toHaveTextContent("Sessão 2 — Return");
    expect(screen.queryByText("No Recap Yet", { exact: false })).not.toBeInTheDocument();
  });

  it("shows an empty state when no session has a summary yet", () => {
    useSessions.mockReturnValue({
      isLoading: false,
      data: [makeSession({ summary: null })],
    });

    render(<RecapPage />);

    expect(screen.getByText("Nenhum resumo de sessão ainda.")).toBeInTheDocument();
  });
});
