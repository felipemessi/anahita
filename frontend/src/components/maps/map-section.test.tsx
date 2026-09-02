import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const useMap = vi.fn();
const useCreateToken = vi.fn();
vi.mock("@/hooks/use-map", () => ({
  useMap: () => useMap(),
  useCreateToken: () => useCreateToken(),
}));

const useCharacter = vi.fn();
vi.mock("@/hooks/use-character", () => ({ useCharacter: () => useCharacter() }));

vi.mock("@/providers/map-provider", () => ({
  MapProvider: ({ children }: { children: React.ReactNode }) => children,
}));

import { MapSection } from "./map-section";
import type { EncounterParticipant } from "@/types/combat";
import type { MapToken, SessionMap } from "@/types/map";

const map: SessionMap = {
  id: "map-1",
  session_id: "sess-1",
  name: "Old Tavern",
  url: "/files/map-1.png",
  width_px: 1000,
  height_px: 1000,
  grid_size_px: 50,
  created_at: "2026-01-01T00:00:00Z",
};

const token: MapToken = {
  id: "token-1",
  map_id: "map-1",
  character_id: "char-1",
  npc_id: null,
  monster_id: null,
  name: "Aria",
  x: 2,
  y: 2,
  is_visible: true,
};

const participant: EncounterParticipant = {
  id: "p-1",
  encounter_id: "enc-1",
  character_id: "char-1",
  npc_id: null,
  monster_id: null,
  name: "Aria",
  initiative: 15,
  hit_point_max: 20,
  hit_point_current: 20,
  temporary_hit_points: 0,
  armor_class: 14,
  turn_order: 0,
  is_active: true,
  conditions: [],
  effects: [],
  concentration_dc: null,
  legendary_actions_used: 0,
  reactions_used: 0,
};

describe("MapSection", () => {
  beforeEach(() => {
    useCreateToken.mockReturnValue({ mutate: vi.fn(), isPending: false });
  });

  it("shows a syncing message before the map snapshot arrives", () => {
    useMap.mockReturnValue({
      map: null,
      tokens: [],
      lastError: null,
      isConnected: false,
      moveToken: vi.fn(),
    });
    useCharacter.mockReturnValue({ data: undefined });

    render(
      <MapSection
        mapId="map-1"
        isDm={false}
        encounterActive={false}
        currentTurnParticipant={undefined}
        participants={[]}
      />,
    );

    expect(screen.getByText("Sincronizando mapa…")).toBeInTheDocument();
  });

  it("renders the map once synced, with the connection status", () => {
    useMap.mockReturnValue({
      map,
      tokens: [token],
      lastError: null,
      isConnected: true,
      moveToken: vi.fn(),
    });
    useCharacter.mockReturnValue({ data: undefined });

    render(
      <MapSection
        mapId="map-1"
        isDm={false}
        encounterActive={false}
        currentTurnParticipant={undefined}
        participants={[participant]}
      />,
    );

    expect(screen.getByText("Old Tavern")).toBeInTheDocument();
    expect(screen.getByText("Conectado")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Token: Aria" })).toBeInTheDocument();
  });

  it("highlights the movement range around the current turn participant's token", () => {
    useMap.mockReturnValue({
      map,
      tokens: [token],
      lastError: null,
      isConnected: true,
      moveToken: vi.fn(),
    });
    useCharacter.mockReturnValue({ data: { speed: 30 } });

    render(
      <MapSection
        mapId="map-1"
        isDm={false}
        encounterActive
        currentTurnParticipant={participant}
        participants={[participant]}
      />,
    );

    // speed 30 -> 6 cells radius -> (2*6+1)^2 = 169 cells around (2,2), clamped to the map.
    expect(screen.getAllByTestId("movement-range-cell").length).toBeGreaterThan(0);
  });

  it("surfaces a rejected move as an alert", () => {
    useMap.mockReturnValue({
      map,
      tokens: [token],
      lastError: "Move of 8 cells exceeds Aria's speed of 6 cells this turn",
      isConnected: true,
      moveToken: vi.fn(),
    });
    useCharacter.mockReturnValue({ data: undefined });

    render(
      <MapSection
        mapId="map-1"
        isDm={false}
        encounterActive={false}
        currentTurnParticipant={undefined}
        participants={[]}
      />,
    );

    expect(screen.getByRole("alert")).toHaveTextContent("exceeds Aria's speed");
  });

  it("clicking a token in selection mode reports the resolved participant id", () => {
    useMap.mockReturnValue({
      map,
      tokens: [token],
      lastError: null,
      isConnected: true,
      moveToken: vi.fn(),
    });
    useCharacter.mockReturnValue({ data: undefined });
    const onSelectedParticipantsChange = vi.fn();

    render(
      <MapSection
        mapId="map-1"
        isDm={false}
        encounterActive={false}
        currentTurnParticipant={undefined}
        participants={[participant]}
        enableTargetSelection
        onSelectedParticipantsChange={onSelectedParticipantsChange}
      />,
    );

    const tokenEl = screen.getByRole("button", { name: "Token: Aria" });
    fireEvent.pointerDown(tokenEl, { clientX: 10, clientY: 10 });
    fireEvent.pointerUp(tokenEl, { clientX: 10, clientY: 10 });

    expect(onSelectedParticipantsChange).toHaveBeenLastCalledWith(["p-1"]);
  });

  it("DM sees an 'add token' shortcut for a participant with no token yet, and it creates one", () => {
    useMap.mockReturnValue({
      map,
      tokens: [],
      lastError: null,
      isConnected: true,
      moveToken: vi.fn(),
    });
    useCharacter.mockReturnValue({ data: undefined });
    const mutate = vi.fn();
    useCreateToken.mockReturnValue({ mutate, isPending: false });

    render(
      <MapSection
        mapId="map-1"
        isDm
        encounterActive={false}
        currentTurnParticipant={undefined}
        participants={[participant]}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "+ Aria" }));

    expect(mutate).toHaveBeenCalledWith({
      character_id: "char-1",
      npc_id: null,
      monster_id: null,
      name: "Aria",
      x: 0,
      y: 0,
    });
  });

  it("a non-DM viewer doesn't see the 'add token' shortcut", () => {
    useMap.mockReturnValue({
      map,
      tokens: [],
      lastError: null,
      isConnected: true,
      moveToken: vi.fn(),
    });
    useCharacter.mockReturnValue({ data: undefined });

    render(
      <MapSection
        mapId="map-1"
        isDm={false}
        encounterActive={false}
        currentTurnParticipant={undefined}
        participants={[participant]}
      />,
    );

    expect(screen.queryByRole("button", { name: "+ Aria" })).not.toBeInTheDocument();
  });
});
