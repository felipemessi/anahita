import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("next/navigation", () => ({
  useParams: () => ({ campaignId: "campaign-1" }),
}));

const useJournalEntries = vi.fn();
vi.mock("@/hooks/use-journal", () => ({
  useJournalEntries: (...args: unknown[]) => useJournalEntries(...args),
  useCreateJournalEntry: () => ({ mutate: vi.fn(), isPending: false, isError: false }),
  useUpdateJournalEntry: () => ({ mutate: vi.fn(), isPending: false, isError: false }),
  useDeleteJournalEntry: () => ({ mutate: vi.fn(), isPending: false, isError: false }),
}));

import JournalPage from "./page";

describe("JournalPage", () => {
  beforeEach(() => {
    useJournalEntries.mockReset();
  });

  it("renders entries and the editor when the request succeeds", () => {
    useJournalEntries.mockReturnValue({
      data: [
        {
          id: "entry-1",
          campaign_id: "campaign-1",
          author_id: "user-1",
          title: "Sessão 1 aftermath",
          content: "The party regroups.",
          session_id: null,
          created_at: "2026-08-24T00:00:00Z",
        },
      ],
      isLoading: false,
      isError: false,
    });

    render(<JournalPage />);

    expect(screen.getByText("Sessão 1 aftermath")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Título da entrada")).toBeInTheDocument();
  });

  it("shows a generic message and no editor when the backend rejects with 403", () => {
    useJournalEntries.mockReturnValue({ data: undefined, isLoading: false, isError: true });

    render(<JournalPage />);

    expect(screen.getByText("Você não tem acesso a esta página.")).toBeInTheDocument();
    expect(screen.queryByPlaceholderText("Título da entrada")).not.toBeInTheDocument();
  });
});
