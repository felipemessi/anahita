import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

vi.mock("next/navigation", () => ({
  useParams: () => ({ campaignId: "camp-1" }),
}));

const useCampaign = vi.fn();
const useMyMembership = vi.fn();
const useMembers = vi.fn();
const useCreateInvite = vi.fn();
const useUpdateCampaign = vi.fn();
vi.mock("@/hooks/use-campaign", () => ({
  useCampaign: (...args: unknown[]) => useCampaign(...args),
  useMyMembership: (...args: unknown[]) => useMyMembership(...args),
  useMembers: (...args: unknown[]) => useMembers(...args),
  useCreateInvite: (...args: unknown[]) => useCreateInvite(...args),
  useUpdateCampaign: (...args: unknown[]) => useUpdateCampaign(...args),
}));

const useUserProfiles = vi.fn();
vi.mock("@/hooks/use-users", () => ({
  useUserProfiles: (...args: unknown[]) => useUserProfiles(...args),
}));

import CampaignSettingsPage from "./page";

const campaign = {
  id: "camp-1",
  name: "Curse of Strahd",
  description: null,
  setting: null,
  owner_id: "user-1",
  status: "active" as const,
  created_at: "2026-01-01T00:00:00Z",
};

function setup(role: "dm" | "player") {
  useCampaign.mockReturnValue({ data: campaign });
  useMyMembership.mockReturnValue({
    data: { id: "mem-1", campaign_id: "camp-1", user_id: "user-1", role, joined_at: "2026-01-01T00:00:00Z" },
  });
  useCreateInvite.mockReturnValue({ mutateAsync: vi.fn(), isPending: false });
  useUpdateCampaign.mockReturnValue({ mutateAsync: vi.fn(), isPending: false });
  useMembers.mockReturnValue({
    data: [
      { id: "mem-1", campaign_id: "camp-1", user_id: "user-1", role: "dm", joined_at: "2026-01-01T00:00:00Z" },
    ],
  });
  useUserProfiles.mockReturnValue({
    data: [{ id: "user-1", email: "dm@anahita.dev", username: "dm" }],
  });

  return render(<CampaignSettingsPage />);
}

describe("CampaignSettingsPage", () => {
  it("shows member management actions for the DM", () => {
    setup("dm");
    expect(
      screen.getByRole("region", { name: /gestão de membros/i }),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /gerar convite/i })).toBeInTheDocument();
  });

  it("hides member management actions for a read-only player", () => {
    setup("player");
    expect(
      screen.queryByRole("region", { name: /gestão de membros/i }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /gerar convite/i }),
    ).not.toBeInTheDocument();
  });

  it("resolves member usernames instead of showing raw user ids", () => {
    setup("dm");
    expect(screen.getByText("dm")).toBeInTheDocument();
    expect(screen.queryByText("user-1")).not.toBeInTheDocument();
  });

  it("lets the DM save general campaign settings", async () => {
    const mutateAsync = vi.fn().mockResolvedValue(campaign);
    useCampaign.mockReturnValue({ data: campaign });
    useMyMembership.mockReturnValue({
      data: {
        id: "mem-1",
        campaign_id: "camp-1",
        user_id: "user-1",
        role: "dm",
        joined_at: "2026-01-01T00:00:00Z",
      },
    });
    useCreateInvite.mockReturnValue({ mutateAsync: vi.fn(), isPending: false });
    useUpdateCampaign.mockReturnValue({ mutateAsync, isPending: false });
    useMembers.mockReturnValue({ data: [] });
    useUserProfiles.mockReturnValue({ data: [] });
    render(<CampaignSettingsPage />);

    fireEvent.change(screen.getByLabelText(/^descrição$/i), {
      target: { value: "Updated description" },
    });
    fireEvent.click(screen.getByRole("button", { name: /^salvar$/i }));

    await waitFor(() => {
      expect(mutateAsync).toHaveBeenCalledWith({
        name: "Curse of Strahd",
        description: "Updated description",
        setting: "",
      });
    });
  });

  it("shows read-only campaign info for a player", () => {
    setup("player");
    expect(screen.queryByLabelText(/^descrição$/i)).not.toBeInTheDocument();
    expect(screen.getAllByText("Curse of Strahd").length).toBeGreaterThan(0);
  });
});
