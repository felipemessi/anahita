"use client";

import { getAccessToken } from "@/lib/api/client";
import type { CombatClientCommand, CombatServerEvent } from "@/lib/ws/types";

const RECONNECT_BASE_DELAY_MS = 1000;
const RECONNECT_MAX_DELAY_MS = 15000;

export interface CombatSocketHandlers {
  onEvent: (event: CombatServerEvent) => void;
  onOpen?: () => void;
  onClose?: () => void;
}

/**
 * Derives the WebSocket origin from `NEXT_PUBLIC_API_URL` (same env var as
 * `lib/api/client.ts`), or falls back to the current page's origin when
 * that var is unset (relative `/api` Nginx proxy setup).
 */
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
 * Wraps the native WebSocket for `/ws/combat/{encounterId}`, with automatic
 * reconnection (exponential backoff, capped). The server always sends a
 * fresh `state_sync` right after a connection is accepted (PRD §10.5), so
 * callers never need to special-case "first connect" vs. "reconnect" —
 * every `state_sync` frame delivered to `onEvent` is the resync point.
 */
export class CombatSocket {
  private socket: WebSocket | null = null;
  private reconnectAttempt = 0;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private closedByCaller = false;

  constructor(
    private readonly encounterId: string,
    private readonly handlers: CombatSocketHandlers,
  ) {}

  connect(): void {
    this.closedByCaller = false;
    const token = getAccessToken() ?? "";
    const url = `${wsBaseUrl()}/ws/combat/${this.encounterId}?token=${encodeURIComponent(token)}`;
    const socket = new WebSocket(url);
    this.socket = socket;

    socket.onopen = () => {
      this.reconnectAttempt = 0;
      this.handlers.onOpen?.();
    };
    socket.onmessage = (event) => {
      try {
        const parsed = JSON.parse(event.data as string) as CombatServerEvent;
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

  send(command: CombatClientCommand): void {
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
