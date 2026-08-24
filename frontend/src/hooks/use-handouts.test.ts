import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import React from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { CombatSocketHandlers } from "@/lib/ws/combat-socket";

const listEncounters = vi.fn();
vi.mock("@/lib/api/combat", () => ({
  listEncounters: (...args: unknown[]) => listEncounters(...args),
}));

const socketConnect = vi.fn();
const socketClose = vi.fn();
let capturedHandlers: CombatSocketHandlers | null = null;

vi.mock("@/lib/ws/combat-socket", () => ({
  CombatSocket: vi.fn().mockImplementation(
    (_encounterId: string, handlers: CombatSocketHandlers) => {
      capturedHandlers = handlers;
      return { connect: socketConnect, close: socketClose, send: vi.fn() };
    },
  ),
}));

import { HANDOUTS_QUERY_KEY, useHandoutRevealListener } from "./use-handouts";

const activeEncounter = {
  id: "enc-1",
  session_id: "sess-1",
  name: "Ambush",
  status: "active" as const,
  current_round: 1,
  current_turn_order: 0,
  created_at: "2026-01-01T00:00:00Z",
  participants: [],
};

function setup() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  const invalidateSpy = vi.spyOn(queryClient, "invalidateQueries");
  const wrapper = ({ children }: { children: React.ReactNode }) =>
    React.createElement(QueryClientProvider, { client: queryClient }, children);
  return { queryClient, invalidateSpy, wrapper };
}

describe("useHandoutRevealListener", () => {
  beforeEach(() => {
    listEncounters.mockReset().mockResolvedValue([activeEncounter]);
    socketConnect.mockClear();
    socketClose.mockClear();
    capturedHandlers = null;
  });

  it("does nothing when there is no session selected", () => {
    const { wrapper } = setup();
    renderHook(() => useHandoutRevealListener("campaign-1", null), { wrapper });

    expect(socketConnect).not.toHaveBeenCalled();
  });

  it("connects to the session's active encounter once it loads", async () => {
    const { wrapper } = setup();
    renderHook(() => useHandoutRevealListener("campaign-1", "sess-1"), { wrapper });

    await waitFor(() => expect(socketConnect).toHaveBeenCalledTimes(1));
  });

  it("invalidates the handout list when a handout_revealed frame arrives", async () => {
    const { wrapper, invalidateSpy } = setup();
    renderHook(() => useHandoutRevealListener("campaign-1", "sess-1"), { wrapper });

    await waitFor(() => expect(capturedHandlers).not.toBeNull());

    capturedHandlers?.onEvent({
      event_type: "handout_revealed",
      payload: { id: "handout-1", title: "Old Map", handout_type: "map", url: "/x" },
    });

    await waitFor(() =>
      expect(invalidateSpy).toHaveBeenCalledWith({
        queryKey: [...HANDOUTS_QUERY_KEY, "campaign-1"],
      }),
    );
  });

  it("ignores other combat frames", async () => {
    const { wrapper, invalidateSpy } = setup();
    renderHook(() => useHandoutRevealListener("campaign-1", "sess-1"), { wrapper });

    await waitFor(() => expect(capturedHandlers).not.toBeNull());
    invalidateSpy.mockClear();

    capturedHandlers?.onEvent({
      event_type: "turn_advanced",
      payload: { round: 2, turn_order: 0, participant_id: null },
    });

    expect(invalidateSpy).not.toHaveBeenCalled();
  });
});
