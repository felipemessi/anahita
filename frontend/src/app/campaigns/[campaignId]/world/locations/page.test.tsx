import { fireEvent, render, screen } from "@testing-library/react";
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

const useLocationTree = vi.fn();
const useLocations = vi.fn();
const useCreateLocation = vi.fn();
const useLinkLocationSession = vi.fn();
vi.mock("@/hooks/use-world", () => ({
  useLocationTree: (...args: unknown[]) => useLocationTree(...args),
  useLocations: (...args: unknown[]) => useLocations(...args),
  useCreateLocation: (...args: unknown[]) => useCreateLocation(...args),
  useLinkLocationSession: (...args: unknown[]) => useLinkLocationSession(...args),
}));

import LocationsPage from "./page";

describe("LocationsPage", () => {
  const linkMutate = vi.fn();

  beforeEach(() => {
    linkMutate.mockClear();
    useLocationTree.mockReturnValue({ data: [], isLoading: false });
    useLocations.mockReturnValue({
      data: [{ id: "loc-1", name: "Waterdeep", location_type: "city" }],
    });
    useMyMembership.mockReturnValue({ data: { role: "dm" } });
    useCreateLocation.mockReturnValue({ mutate: vi.fn(), isPending: false, isError: false });
    useLinkLocationSession.mockReturnValue({ mutate: linkMutate, isPending: false });
    useSessions.mockReturnValue({
      data: [{ id: "sess-1", session_number: 1, title: "The Beginning" }],
    });
  });

  it("lets the DM link a location to a session visit", () => {
    render(<LocationsPage />);

    fireEvent.change(screen.getByLabelText(/local a vincular a uma sessão/i), {
      target: { value: "loc-1" },
    });
    fireEvent.change(screen.getByLabelText(/sessão visitada/i), {
      target: { value: "sess-1" },
    });
    fireEvent.click(screen.getByRole("button", { name: /^vincular$/i }));

    expect(linkMutate).toHaveBeenCalledWith(
      { session_id: "sess-1" },
      expect.anything(),
    );
  });
});
