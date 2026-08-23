import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const push = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push }),
}));

const listCampaigns = vi.fn();
const createCampaign = vi.fn();
const redeemInvite = vi.fn();
vi.mock("@/lib/api/campaigns", () => ({
  listCampaigns: (...args: unknown[]) => listCampaigns(...args),
  createCampaign: (...args: unknown[]) => createCampaign(...args),
  redeemInvite: (...args: unknown[]) => redeemInvite(...args),
}));

const getCurrentUser = vi.fn();
vi.mock("@/lib/auth/session", () => ({
  getCurrentUser: (...args: unknown[]) => getCurrentUser(...args),
}));

import CampaignsPage from "./page";

function renderWithClient() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <CampaignsPage />
    </QueryClientProvider>,
  );
}

describe("CampaignsPage", () => {
  beforeEach(() => {
    push.mockClear();
    listCampaigns.mockReset();
    createCampaign.mockReset();
    redeemInvite.mockReset();
    getCurrentUser.mockReset();
    getCurrentUser.mockResolvedValue({
      id: "user-1",
      email: "dm@anahita.dev",
      username: "dm",
    });
  });

  it("renders the user's campaigns with role and status", async () => {
    listCampaigns.mockResolvedValueOnce([
      {
        id: "camp-1",
        name: "Curse of Strahd",
        description: null,
        setting: null,
        owner_id: "user-1",
        status: "active",
        created_at: "2026-01-01T00:00:00Z",
      },
    ]);

    renderWithClient();

    expect(await screen.findByText("Curse of Strahd")).toBeInTheDocument();
    expect(
      screen.getByText((_, el) => el?.textContent === "Mestre · Ativa"),
    ).toBeInTheDocument();
  });

  it("creates a campaign and redirects to its dashboard", async () => {
    listCampaigns.mockResolvedValue([]);
    createCampaign.mockResolvedValueOnce({
      id: "camp-2",
      name: "New Campaign",
      description: null,
      setting: null,
      owner_id: "user-1",
      status: "active",
      created_at: "2026-01-01T00:00:00Z",
    });

    renderWithClient();
    await screen.findByText(/você ainda não participa/i);

    fireEvent.change(screen.getByLabelText(/nome da campanha/i), {
      target: { value: "New Campaign" },
    });
    fireEvent.click(screen.getByRole("button", { name: /criar campanha/i }));

    await waitFor(() => {
      expect(createCampaign).toHaveBeenCalledWith({ name: "New Campaign" });
      expect(push).toHaveBeenCalledWith("/campaigns/camp-2");
    });
  });
});
