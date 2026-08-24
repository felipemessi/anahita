import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

const useRevealHandout = vi.fn();
vi.mock("@/hooks/use-handouts", () => ({
  useRevealHandout: (...args: unknown[]) => useRevealHandout(...args),
}));

import { HandoutCard } from "./handout-card";
import type { Handout } from "@/types/handout";

const textHandout: Handout = {
  id: "handout-1",
  campaign_id: "campaign-1",
  session_id: null,
  title: "Old Rumor",
  content: "The tavern keeper knows something.",
  handout_type: "text",
  url: null,
  is_revealed: false,
  revealed_at: null,
  created_at: "2026-01-01T00:00:00Z",
};

describe("HandoutCard", () => {
  it("shows a reveal button for the DM when not yet revealed", () => {
    useRevealHandout.mockReturnValue({ mutate: vi.fn(), isPending: false });
    render(<HandoutCard handout={textHandout} campaignId="campaign-1" isDm />);

    expect(screen.getByRole("button", { name: /revelar/i })).toBeInTheDocument();
  });

  it("hides the reveal button for a player", () => {
    useRevealHandout.mockReturnValue({ mutate: vi.fn(), isPending: false });
    render(<HandoutCard handout={textHandout} campaignId="campaign-1" isDm={false} />);

    expect(screen.queryByRole("button", { name: /revelar/i })).not.toBeInTheDocument();
  });

  it("hides the reveal button once already revealed", () => {
    useRevealHandout.mockReturnValue({ mutate: vi.fn(), isPending: false });
    render(
      <HandoutCard
        handout={{ ...textHandout, is_revealed: true }}
        campaignId="campaign-1"
        isDm
      />,
    );

    expect(screen.queryByRole("button", { name: /revelar/i })).not.toBeInTheDocument();
  });

  it("expands to show the content when toggled", () => {
    useRevealHandout.mockReturnValue({ mutate: vi.fn(), isPending: false });
    render(<HandoutCard handout={textHandout} campaignId="campaign-1" isDm={false} />);

    expect(screen.queryByText(textHandout.content!)).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /ver/i }));
    expect(screen.getByText(textHandout.content!)).toBeInTheDocument();
  });
});
