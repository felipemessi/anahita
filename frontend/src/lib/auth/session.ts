"use client";

import { apiFetch, setAccessToken } from "@/lib/api/client";

/** Minimal identity decoded from the access token's JWT payload. */
export interface SessionUser {
  id: string;
}

interface TokenResponse {
  access_token: string;
  token_type: string;
}

/**
 * Decode a JWT payload without verifying its signature. Safe here because
 * the token itself was already validated by the backend that issued it —
 * this is only used to read the `sub` claim for UI purposes, never to
 * authorize anything client-side.
 */
function decodeAccessToken(token: string): SessionUser | null {
  try {
    const [, payload] = token.split(".");
    if (!payload) return null;
    const json = JSON.parse(atob(payload.replace(/-/g, "+").replace(/_/g, "/"))) as {
      sub?: string;
    };
    return json.sub ? { id: json.sub } : null;
  } catch {
    return null;
  }
}

/** Log in with email + password. Stores the access token in memory and returns the session user. */
export async function login(
  email: string,
  password: string,
): Promise<SessionUser> {
  const { access_token } = await apiFetch<TokenResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
    skipAuthRefresh: true,
  });
  setAccessToken(access_token);
  const user = decodeAccessToken(access_token);
  if (!user) {
    throw new Error("Received an invalid access token");
  }
  return user;
}

/** Register a new account. Does not log the user in automatically. */
export async function register(
  email: string,
  username: string,
  password: string,
): Promise<void> {
  await apiFetch<unknown>("/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, username, password }),
    skipAuthRefresh: true,
  });
}

/** Revoke the refresh token server-side and clear the in-memory access token. */
export async function logout(): Promise<void> {
  await apiFetch<unknown>("/auth/logout", {
    method: "POST",
    skipAuthRefresh: true,
  }).catch(() => {
    // Best-effort: still clear local state even if the request fails.
  });
  setAccessToken(null);
}
