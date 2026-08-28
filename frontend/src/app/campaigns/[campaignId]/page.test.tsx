import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("next/navigation", () => ({
  useParams: () => ({ campaignId: "camp-1" }),
}));

const useCampaign = vi.fn();
const useMyMembership = vi.fn();
const useCampaignDashboard = vi.fn();
vi.mock("@/hooks/use-campaign", () => ({
  useCampaign: (...args: unknown[]) => useCampaign(...args),
  useMyMembership: (...args: unknown[]) => useMyMembership(...args),
  useCampaignDashboard: (...args: unknown[]) => useCampaignDashboard(...args),
}));

const useCharacters = vi.fn();
vi.mock("@/hooks/use-character", () => ({
  useCharacters: (...args: unknown[]) => useCharacters(...args),
}));

import CampaignDashboardPage from "./page";

const campaign = {
  id: "camp-1",
  name: "Waterdeep",
  description: null,
  setting: null,
  owner_id: "u-dm",
  status: "active",
  created_at: "2026-01-01T00:00:00Z",
};

const dmMember = { id: "member-dm", campaign_id: "camp-1", user_id: "u-dm", role: "dm" };
const playerMember = {
  id: "member-1",
  campaign_id: "camp-1",
  user_id: "u-1",
  role: "player",
};

const nextSession = {
  id: "sess-1",
  campaign_id: "camp-1",
  session_number: 4,
  title: "A Torre Caída",
  scheduled_date: "2026-09-01",
  status: "planned",
  dm_notes: null,
  summary: null,
  created_at: "2026-08-01T00:00:00Z",
};

const dashboard = {
  next_session: nextSession,
  recent_npcs: [
    {
      id: "npc-1",
      campaign_id: "camp-1",
      name: "Renata",
      race: "human",
      occupation: null,
      description: "",
      personality: null,
      is_alive: true,
      stat_block_id: null,
      created_at: "2026-08-01T00:00:00Z",
    },
  ],
  recent_locations: [
    {
      id: "loc-1",
      campaign_id: "camp-1",
      name: "Taverna do Corvo",
      location_type: "building",
      description: "",
      parent_location_id: null,
      created_at: "2026-08-01T00:00:00Z",
    },
  ],
  pending_handouts: [
    { id: "handout-1", title: "Mapa do Porão", handout_type: "map", created_at: "" },
  ],
  pending_handouts_count: 1,
};

describe("CampaignDashboardPage", () => {
  beforeEach(() => {
    useCampaign.mockReturnValue({ data: campaign, isLoading: false });
    useCharacters.mockReturnValue({ data: [] });
  });

  it("renders the next session for the DM", () => {
    useMyMembership.mockReturnValue({ data: dmMember });
    useCampaignDashboard.mockReturnValue({ data: dashboard, isLoading: false });

    render(<CampaignDashboardPage />);

    expect(screen.getByText(/A Torre Caída/)).toBeInTheDocument();
  });

  it("renders recent NPCs and locations for the DM", () => {
    useMyMembership.mockReturnValue({ data: dmMember });
    useCampaignDashboard.mockReturnValue({ data: dashboard, isLoading: false });

    render(<CampaignDashboardPage />);

    expect(screen.getByText("Renata")).toBeInTheDocument();
    expect(screen.getByText("Taverna do Corvo")).toBeInTheDocument();
  });

  it("renders pending handouts for the DM", () => {
    useMyMembership.mockReturnValue({ data: dmMember });
    useCampaignDashboard.mockReturnValue({ data: dashboard, isLoading: false });

    render(<CampaignDashboardPage />);

    expect(screen.getByText("Mapa do Porão")).toBeInTheDocument();
    expect(screen.getByText(/1 não revelado/)).toBeInTheDocument();
  });

  it("never shows the pending-handouts section to a player", () => {
    useMyMembership.mockReturnValue({ data: playerMember });
    useCampaignDashboard.mockReturnValue({
      data: { ...dashboard, pending_handouts: [], pending_handouts_count: 0 },
      isLoading: false,
    });

    render(<CampaignDashboardPage />);

    expect(screen.queryByText("Handouts pendentes")).not.toBeInTheDocument();
    expect(screen.getByText(/A Torre Caída/)).toBeInTheDocument();
  });

  it("renders the next session even when it has no scheduled date", () => {
    useMyMembership.mockReturnValue({ data: dmMember });
    useCampaignDashboard.mockReturnValue({
      data: {
        ...dashboard,
        next_session: { ...nextSession, scheduled_date: null },
      },
      isLoading: false,
    });

    render(<CampaignDashboardPage />);

    expect(screen.getByText(/A Torre Caída/)).toBeInTheDocument();
    expect(screen.queryByText("2026-09-01")).not.toBeInTheDocument();
  });

  it("shows a placeholder when there is no upcoming session", () => {
    useMyMembership.mockReturnValue({ data: dmMember });
    useCampaignDashboard.mockReturnValue({
      data: { ...dashboard, next_session: null },
      isLoading: false,
    });

    render(<CampaignDashboardPage />);

    expect(screen.getByText(/Nenhuma sessão futura agendada/)).toBeInTheDocument();
  });
});
