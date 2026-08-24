import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

vi.mock("next/navigation", () => ({
  usePathname: () => "/campaigns/campaign-1",
}));

import { CampaignSidebar } from "./campaign-sidebar";

describe("CampaignSidebar", () => {
  it("shows the DM-only Diário item for the DM", () => {
    render(<CampaignSidebar campaignId="campaign-1" role="dm" />);

    expect(screen.getByText("Diário")).toBeInTheDocument();
  });

  it("hides the DM-only Diário item entirely for a player", () => {
    render(<CampaignSidebar campaignId="campaign-1" role="player" />);

    expect(screen.queryByText("Diário")).not.toBeInTheDocument();
  });
});
