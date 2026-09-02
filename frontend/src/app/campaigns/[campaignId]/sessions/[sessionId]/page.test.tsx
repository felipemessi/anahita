import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("next/navigation", () => ({
  useParams: () => ({ campaignId: "camp-1", sessionId: "sess-1" }),
}));

const useMyMembership = vi.fn();
vi.mock("@/hooks/use-campaign", () => ({
  useMyMembership: (...args: unknown[]) => useMyMembership(...args),
}));

const useSessions = vi.fn();
const useOpenSession = vi.fn();
const useCompleteSession = vi.fn();
const useUpdateSession = vi.fn();
vi.mock("@/hooks/use-session", () => ({
  useSessions: (...args: unknown[]) => useSessions(...args),
  useOpenSession: (...args: unknown[]) => useOpenSession(...args),
  useCompleteSession: (...args: unknown[]) => useCompleteSession(...args),
  useUpdateSession: (...args: unknown[]) => useUpdateSession(...args),
}));

const useEncounters = vi.fn();
const useCreateEncounter = vi.fn();
const useStartEncounter = vi.fn();
vi.mock("@/hooks/use-combat", () => ({
  useEncounters: (...args: unknown[]) => useEncounters(...args),
  useCreateEncounter: (...args: unknown[]) => useCreateEncounter(...args),
  useStartEncounter: (...args: unknown[]) => useStartEncounter(...args),
}));

vi.mock("@/components/sessions/note-editor", () => ({
  NoteEditor: () => null,
}));

const useMaps = vi.fn();
vi.mock("@/hooks/use-map", () => ({
  useMaps: (...args: unknown[]) => useMaps(...args),
}));
vi.mock("@/components/maps/map-section", () => ({ MapSection: () => null }));
vi.mock("@/components/maps/map-upload", () => ({ MapUpload: () => null }));

import SessionDetailPage from "./page";

const plannedSession = {
  id: "sess-1",
  campaign_id: "camp-1",
  session_number: 1,
  title: "A Emboscada",
  scheduled_date: null,
  status: "planned" as const,
  dm_notes: null,
  summary: null,
  created_at: "2026-01-01T00:00:00Z",
};

describe("SessionDetailPage", () => {
  const openSessionMutate = vi.fn();
  const completeSessionMutate = vi.fn();
  const updateSessionMutate = vi.fn();

  beforeEach(() => {
    openSessionMutate.mockReset();
    completeSessionMutate.mockReset();
    updateSessionMutate.mockReset();
    useSessions.mockReturnValue({ data: [plannedSession], isLoading: false });
    useEncounters.mockReturnValue({ data: [] });
    useCreateEncounter.mockReturnValue({ mutate: vi.fn(), isPending: false });
    useStartEncounter.mockReturnValue({ mutate: vi.fn(), isPending: false });
    useOpenSession.mockReturnValue({ mutate: openSessionMutate, isPending: false });
    useCompleteSession.mockReturnValue({ mutate: completeSessionMutate, isPending: false });
    useUpdateSession.mockReturnValue({ mutate: updateSessionMutate, isPending: false });
    useMaps.mockReturnValue({ data: [] });
  });

  it("the DM sees an 'Abrir sessão' button for a planned session", () => {
    useMyMembership.mockReturnValue({ data: { role: "dm" } });

    render(<SessionDetailPage />);

    fireEvent.click(screen.getByRole("button", { name: "Abrir sessão" }));

    expect(openSessionMutate).toHaveBeenCalledWith("sess-1");
  });

  it("a player doesn't see the 'Abrir sessão' button, only the status", () => {
    useMyMembership.mockReturnValue({ data: { role: "player" } });

    render(<SessionDetailPage />);

    expect(screen.queryByRole("button", { name: "Abrir sessão" })).not.toBeInTheDocument();
    expect(screen.getByText("Planejada")).toBeInTheDocument();
  });

  it("the DM doesn't see the button once the session is already open", () => {
    useMyMembership.mockReturnValue({ data: { role: "dm" } });
    useSessions.mockReturnValue({
      data: [{ ...plannedSession, status: "in_progress" }],
      isLoading: false,
    });

    render(<SessionDetailPage />);

    expect(screen.queryByRole("button", { name: "Abrir sessão" })).not.toBeInTheDocument();
    expect(screen.getByText("Em andamento")).toBeInTheDocument();
  });

  it("the DM sees a 'Concluir sessão' button for an in-progress session and it completes it", () => {
    useMyMembership.mockReturnValue({ data: { role: "dm" } });
    useSessions.mockReturnValue({
      data: [{ ...plannedSession, status: "in_progress" }],
      isLoading: false,
    });

    render(<SessionDetailPage />);

    fireEvent.click(screen.getByRole("button", { name: "Concluir sessão" }));

    expect(completeSessionMutate).toHaveBeenCalledWith("sess-1");
  });

  it("a player doesn't see the 'Concluir sessão' button", () => {
    useMyMembership.mockReturnValue({ data: { role: "player" } });
    useSessions.mockReturnValue({
      data: [{ ...plannedSession, status: "in_progress" }],
      isLoading: false,
    });

    render(<SessionDetailPage />);

    expect(
      screen.queryByRole("button", { name: "Concluir sessão" }),
    ).not.toBeInTheDocument();
  });

  it("the DM can edit and save the session title", () => {
    useMyMembership.mockReturnValue({ data: { role: "dm" } });

    render(<SessionDetailPage />);

    fireEvent.click(screen.getByRole("button", { name: "Editar" }));

    const input = screen.getByDisplayValue("A Emboscada");
    fireEvent.change(input, { target: { value: "A Nova Emboscada" } });
    fireEvent.click(screen.getByRole("button", { name: "Salvar" }));

    expect(updateSessionMutate).toHaveBeenCalledWith(
      { sessionId: "sess-1", data: { title: "A Nova Emboscada" } },
      expect.objectContaining({ onSuccess: expect.any(Function) }),
    );
  });

  it("a player doesn't see the title 'Editar' button", () => {
    useMyMembership.mockReturnValue({ data: { role: "player" } });

    render(<SessionDetailPage />);

    expect(screen.queryByRole("button", { name: "Editar" })).not.toBeInTheDocument();
  });
});
