"use client";

import { getAccessToken } from "@/lib/api/client";
import type { MapClientCommand, MapServerEvent } from "@/lib/ws/map-types";

const RECONNECT_BASE_DELAY_MS = 1000;
const RECONNECT_MAX_DELAY_MS = 15000;

export interface MapSocketHandlers {
  onEvent: (event: MapServerEvent) => void;
  onOpen?: () => void;
  onClose?: () => void;
}

/** Same derivation as lib/ws/combat-socket.ts's `wsBaseUrl` — kept local to avoid a shared abstraction for one line of logic. */
function wsBaseUrl(): string {
  const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL;
  if (apiBaseUrl) {
    return apiBaseUrl.replace(/^http/, "ws");
  }
  if (typeof window !== "undefined") {
    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    return `${protocol}://${window.location.host}/api`;
  }
  return "ws://localhost:8000";
}

/**
 * Wraps the native WebSocket for `/ws/map/{mapId}`, with automatic
 * reconnection (exponential backoff, capped) — same shape as `CombatSocket`,
 * a separate class since maps have their own connection registry
 * (`app.maps.ws_manager`, distinct from combat's) and no shared event/command
 * union with it.
 */
export class MapSocket {
  private socket: WebSocket | null = null;
  private reconnectAttempt = 0;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private closedByCaller = false;

  constructor(
    private readonly mapId: string,
    private readonly handlers: MapSocketHandlers,
  ) {}

  connect(): void {
    this.closedByCaller = false;
    const token = getAccessToken() ?? "";
    const url = `${wsBaseUrl()}/ws/map/${this.mapId}?token=${encodeURIComponent(token)}`;
    const socket = new WebSocket(url);
    this.socket = socket;

    socket.onopen = () => {
      this.reconnectAttempt = 0;
      this.handlers.onOpen?.();
    };
    socket.onmessage = (event) => {
      try {
        const parsed = JSON.parse(event.data as string) as MapServerEvent;
        this.handlers.onEvent(parsed);
      } catch {
        // Malformed frame — ignore rather than crash the socket handler.
      }
    };
    socket.onclose = () => {
      this.handlers.onClose?.();
      if (!this.closedByCaller) this.scheduleReconnect();
    };
    socket.onerror = () => {
      socket.close();
    };
  }

  private scheduleReconnect(): void {
    const delay = Math.min(
      RECONNECT_BASE_DELAY_MS * 2 ** this.reconnectAttempt,
      RECONNECT_MAX_DELAY_MS,
    );
    this.reconnectAttempt += 1;
    this.reconnectTimer = setTimeout(() => this.connect(), delay);
  }

  send(command: MapClientCommand): void {
    this.socket?.send(JSON.stringify(command));
  }

  close(): void {
    this.closedByCaller = true;
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    this.reconnectTimer = null;
    this.socket?.close();
    this.socket = null;
  }
}
