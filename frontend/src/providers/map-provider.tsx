"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useReducer,
  useRef,
  useState,
} from "react";

import { MapSocket } from "@/lib/ws/map-socket";
import type { MapClientCommand, MapServerEvent } from "@/lib/ws/map-types";
import type { MapToken, SessionMap } from "@/types/map";

export interface MapState {
  map: SessionMap | null;
  tokens: MapToken[];
  lastError: string | null;
}

export const initialMapState: MapState = {
  map: null,
  tokens: [],
  lastError: null,
};

/**
 * Pure reducer over the server events, exported for unit testing without
 * mounting the provider/socket — mirrors `combatReducer`. `state_sync`
 * replaces the whole snapshot (first connect and every reconnect); the
 * other events patch `tokens` incrementally.
 */
export function mapReducer(state: MapState, event: MapServerEvent): MapState {
  switch (event.event_type) {
    case "state_sync":
      return {
        ...state,
        map: event.payload.map,
        tokens: event.payload.tokens,
        lastError: null,
      };

    case "token_added":
      return { ...state, tokens: [...state.tokens, event.payload] };

    case "token_moved": {
      const updated = event.payload;
      return {
        ...state,
        tokens: state.tokens.map((token) => (token.id === updated.id ? updated : token)),
      };
    }

    case "token_removed":
      return {
        ...state,
        tokens: state.tokens.filter((token) => token.id !== event.payload.id),
      };

    case "error":
      return { ...state, lastError: event.payload.detail };

    default:
      return state;
  }
}

interface MapContextValue extends MapState {
  isConnected: boolean;
  sendCommand: (command: MapClientCommand) => void;
}

const MapContext = createContext<MapContextValue | null>(null);

/** Opens (and keeps open) the map WebSocket for `mapId` for its lifetime. */
export function MapProvider({
  mapId,
  children,
}: {
  mapId: string;
  children: React.ReactNode;
}) {
  const [state, dispatch] = useReducer(mapReducer, initialMapState);
  const [isConnected, setIsConnected] = useState(false);
  const socketRef = useRef<MapSocket | null>(null);

  useEffect(() => {
    const socket = new MapSocket(mapId, {
      onEvent: (event) => dispatch(event),
      onOpen: () => setIsConnected(true),
      onClose: () => setIsConnected(false),
    });
    socketRef.current = socket;
    socket.connect();

    return () => {
      socket.close();
      socketRef.current = null;
    };
  }, [mapId]);

  const sendCommand = useCallback((command: MapClientCommand) => {
    socketRef.current?.send(command);
  }, []);

  const value: MapContextValue = { ...state, isConnected, sendCommand };

  return <MapContext.Provider value={value}>{children}</MapContext.Provider>;
}

/** Access the current map state and command sender. Must be used within `MapProvider`. */
export function useMapContext(): MapContextValue {
  const context = useContext(MapContext);
  if (!context) {
    throw new Error("useMapContext must be used within a MapProvider");
  }
  return context;
}
