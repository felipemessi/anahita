import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("next/navigation", () => ({
  useParams: () => ({ campaignId: "campaign-1" }),
}));

const useTimeline = vi.fn();
const useMyMembership = vi.fn();
const useSessions = vi.fn();
const createMutate = vi.fn();
vi.mock("@/hooks/use-timeline", () => ({
  useTimeline: (...args: unknown[]) => useTimeline(...args),
  useCreateTimelineEvent: () => ({
    mutate: createMutate,
    isPending: false,
    isError: false,
  }),
  useDeleteTimelineEvent: () => ({ mutate: vi.fn(), isPending: false }),
}));
vi.mock("@/hooks/use-campaign", () => ({
  useMyMembership: (...args: unknown[]) => useMyMembership(...args),
}));
vi.mock("@/hooks/use-session", () => ({
  useSessions: (...args: unknown[]) => useSessions(...args),
}));

import TimelinePage from "./page";

describe("TimelinePage", () => {
  beforeEach(() => {
    useTimeline.mockReset();
    useMyMembership.mockReset();
    useSessions.mockReturnValue({ data: [] });
    useTimeline.mockReturnValue({
      isLoading: false,
      data: [
        {
          entry_type: "session",
          id: "s1",
          title: "Sessão 1",
          description: "They arrive.",
          session_id: "s1",
          in_game_date: null,
          sort_order: 1000,
          created_at: "2026-08-24T00:00:00Z",
        },
        {
          entry_type: "event",
          id: "e1",
          title: "A prophecy foretold",
          description: null,
          session_id: null,
          in_game_date: "Year 1412",
          sort_order: 1500,
          created_at: "2026-08-24T00:00:00Z",
        },
      ],
    });
  });

  it("renders automatic and manual entries together, in the order returned", () => {
    useMyMembership.mockReturnValue({ data: { role: "player" } });

    render(<TimelinePage />);

    const items = screen.getAllByRole("listitem");
    expect(items).toHaveLength(2);
    expect(items[0]).toHaveTextContent("Sessão 1");
    expect(items[1]).toHaveTextContent("A prophecy foretold");
  });

  it("only shows the manual-event creation form to the DM", () => {
    useMyMembership.mockReturnValue({ data: { role: "player" } });
    render(<TimelinePage />);
    expect(screen.queryByPlaceholderText("Título")).not.toBeInTheDocument();

    useMyMembership.mockReturnValue({ data: { role: "dm" } });
    render(<TimelinePage />);
    expect(screen.getByPlaceholderText("Título")).toBeInTheDocument();
  });

  it("lets the DM submit a manual event with title and sort order", () => {
    useMyMembership.mockReturnValue({ data: { role: "dm" } });
    render(<TimelinePage />);

    fireEvent.change(screen.getByPlaceholderText("Título"), {
      target: { value: "New marker" },
    });
    fireEvent.change(screen.getByLabelText("Posição de ordenação"), {
      target: { value: "1200" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Adicionar marco" }));

    expect(createMutate).toHaveBeenCalledWith(
      expect.objectContaining({ title: "New marker", sort_order: 1200 }),
      expect.anything(),
    );
  });
});
