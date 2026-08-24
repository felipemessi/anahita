import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("next/navigation", () => ({
  useParams: () => ({ campaignId: "campaign-1" }),
}));

const useMyMembership = vi.fn();
vi.mock("@/hooks/use-campaign", () => ({
  useMyMembership: (...args: unknown[]) => useMyMembership(...args),
}));

const useSessions = vi.fn();
vi.mock("@/hooks/use-session", () => ({
  useSessions: (...args: unknown[]) => useSessions(...args),
}));

const useHandouts = vi.fn();
const useCreateHandout = vi.fn();
const useRevealHandout = vi.fn();
const useHandoutRevealListener = vi.fn();
vi.mock("@/hooks/use-handouts", () => ({
  useHandouts: (...args: unknown[]) => useHandouts(...args),
  useCreateHandout: (...args: unknown[]) => useCreateHandout(...args),
  useRevealHandout: (...args: unknown[]) => useRevealHandout(...args),
  useHandoutRevealListener: (...args: unknown[]) => useHandoutRevealListener(...args),
}));

import HandoutsPage from "./page";
import type { Handout } from "@/types/handout";

const revealed: Handout = {
  id: "handout-1",
  campaign_id: "campaign-1",
  session_id: null,
  title: "Public note",
  content: "Everyone can read this.",
  handout_type: "text",
  url: null,
  is_revealed: true,
  revealed_at: "2026-01-01T00:00:00Z",
  created_at: "2026-01-01T00:00:00Z",
};

const hidden: Handout = {
  ...revealed,
  id: "handout-2",
  title: "Hidden note",
  is_revealed: false,
  revealed_at: null,
};

describe("HandoutsPage", () => {
  beforeEach(() => {
    useSessions.mockReturnValue({ data: [] });
    useCreateHandout.mockReturnValue({ mutate: vi.fn(), isPending: false });
    useRevealHandout.mockReturnValue({ mutate: vi.fn(), isPending: false });
    useHandoutRevealListener.mockReturnValue(undefined);
  });

  it("shows the create form for the DM", () => {
    useMyMembership.mockReturnValue({ data: { id: "mem-1", role: "dm" } });
    useHandouts.mockReturnValue({ data: [revealed, hidden], isLoading: false });

    render(<HandoutsPage />);

    expect(screen.getByPlaceholderText("Título")).toBeInTheDocument();
    expect(screen.getByText("Public note")).toBeInTheDocument();
    expect(screen.getByText("Hidden note")).toBeInTheDocument();
  });

  it("hides the create form for a player and only shows revealed handouts", () => {
    useMyMembership.mockReturnValue({ data: { id: "mem-2", role: "player" } });
    // The backend already filters unrevealed handouts out for non-DM members —
    // the player's query result never contains `hidden`.
    useHandouts.mockReturnValue({ data: [revealed], isLoading: false });

    render(<HandoutsPage />);

    expect(screen.queryByPlaceholderText("Título")).not.toBeInTheDocument();
    expect(screen.getByText("Public note")).toBeInTheDocument();
    expect(screen.queryByText("Hidden note")).not.toBeInTheDocument();
  });
});
