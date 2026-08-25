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

import { CombatSocket } from "@/lib/ws/combat-socket";
import type {
  CombatClientCommand,
  CombatServerEvent,
  DeclareActionResult,
} from "@/lib/ws/types";
import type { Encounter } from "@/types/combat";

/** Most recent `declare_action` results kept for `ActionLog` — newest first. */
const MAX_ACTION_LOG_ENTRIES = 10;

export interface CombatState {
  encounter: Encounter | null;
  lastError: string | null;
  actionLog: DeclareActionResult[];
}

export const initialCombatState: CombatState = {
  encounter: null,
  lastError: null,
  actionLog: [],
};

/**
 * Pure reducer over the server events, exported for unit testing without
 * mounting the provider/socket. `state_sync` replaces the whole encounter
 * (used both on first connect and after a reconnect); the other events
 * patch it incrementally.
 */
export function combatReducer(
  state: CombatState,
  event: CombatServerEvent,
): CombatState {
  switch (event.event_type) {
    case "state_sync":
      return { ...state, encounter: event.payload, lastError: null };

    case "turn_advanced": {
      if (!state.encounter) return state;
      return {
        ...state,
        encounter: {
          ...state.encounter,
          current_round: event.payload.round,
          current_turn_order: event.payload.turn_order,
        },
      };
    }

    case "participant_updated": {
      if (!state.encounter) return state;
      const updated = event.payload;
      return {
        ...state,
        encounter: {
          ...state.encounter,
          participants: state.encounter.participants.map((participant) =>
            participant.id === updated.id ? updated : participant,
          ),
        },
      };
    }

    case "encounter_status_changed": {
      if (!state.encounter) return state;
      return {
        ...state,
        encounter: { ...state.encounter, status: event.payload.status },
      };
    }

    case "action_resolved":
      return {
        ...state,
        actionLog: [event.payload, ...state.actionLog].slice(0, MAX_ACTION_LOG_ENTRIES),
      };

    case "error":
      return { ...state, lastError: event.payload.detail };

    default:
      return state;
  }
}

interface CombatContextValue extends CombatState {
  isConnected: boolean;
  sendCommand: (command: CombatClientCommand) => void;
}

const CombatContext = createContext<CombatContextValue | null>(null);

/** Opens (and keeps open) the combat WebSocket for `encounterId` for its lifetime. */
export function CombatProvider({
  encounterId,
  children,
}: {
  encounterId: string;
  children: React.ReactNode;
}) {
  const [state, dispatch] = useReducer(combatReducer, initialCombatState);
  const [isConnected, setIsConnected] = useState(false);
  const socketRef = useRef<CombatSocket | null>(null);

  useEffect(() => {
    const socket = new CombatSocket(encounterId, {
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
  }, [encounterId]);

  const sendCommand = useCallback((command: CombatClientCommand) => {
    socketRef.current?.send(command);
  }, []);

  const value: CombatContextValue = { ...state, isConnected, sendCommand };

  return <CombatContext.Provider value={value}>{children}</CombatContext.Provider>;
}

/** Access the current combat state and command sender. Must be used within `CombatProvider`. */
export function useCombatContext(): CombatContextValue {
  const context = useContext(CombatContext);
  if (!context) {
    throw new Error("useCombatContext must be used within a CombatProvider");
  }
  return context;
}
