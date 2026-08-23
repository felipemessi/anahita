"use client";

import { apiFetch, setAccessToken } from "@/lib/api/client";

/** Public profile of the authenticated user — mirrors backend UserPublic (GET /auth/me). */
export interface SessionUser {
  id: string;
  email: string;
  username: string;
}

interface TokenResponse {
  access_token: string;
  token_type: string;
}

/** Fetch the authenticated user's profile from GET /auth/me. */
export async function getCurrentUser(): Promise<SessionUser> {
  return apiFetch<SessionUser>("/auth/me");
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
  return getCurrentUser();
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
