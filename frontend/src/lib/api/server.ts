import "server-only";

import { cookies } from "next/headers";
import { cache } from "react";

/**
 * Server-side API client for Server Components. Propagates the httpOnly
 * refresh-token cookie to mint a fresh access token per request (React
 * `cache()` de-dupes this within a single render pass), then attaches it as
 * a Bearer token on the actual request.
 *
 * See docs/anahita-frontend-prd.md §4.2.
 */

const API_BASE_URL = process.env.ANAHITA_API_URL ?? "http://backend:8000";
const REFRESH_COOKIE = "refresh_token";

/** Resolve a fresh access token for the current request, or null if unauthenticated. */
export const getServerAccessToken = cache(async (): Promise<string | null> => {
  const cookieStore = await cookies();
  const refreshToken = cookieStore.get(REFRESH_COOKIE)?.value;
  if (!refreshToken) {
    return null;
  }

  const res = await fetch(`${API_BASE_URL}/auth/refresh`, {
    method: "POST",
    headers: { Cookie: `${REFRESH_COOKIE}=${refreshToken}` },
    cache: "no-store",
  });

  if (!res.ok) {
    return null;
  }

  const data = (await res.json()) as { access_token: string };
  return data.access_token;
});

export class ServerApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = "ServerApiError";
  }
}

export interface ServerApiFetchOptions extends RequestInit {
  /** Catalog locale (`en`, `pt-BR`, …) to append as `?locale=` — see lib/api/catalog.ts. */
  locale?: string;
}

/** Authenticated fetch for use inside Server Components / route handlers. */
export async function serverApiFetch<T>(
  path: string,
  { locale, ...init }: ServerApiFetchOptions = {},
): Promise<T> {
  const accessToken = await getServerAccessToken();
  const url = locale
    ? `${path}${path.includes("?") ? "&" : "?"}locale=${encodeURIComponent(locale)}`
    : path;

  const res = await fetch(`${API_BASE_URL}${url}`, {
    ...init,
    cache: "no-store",
    headers: {
      "Content-Type": "application/json",
      ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
      ...init.headers,
    },
  });

  if (!res.ok) {
    const body = await res.json().catch(() => null);
    const message =
      (body as { detail?: string } | null)?.detail ?? res.statusText;
    throw new ServerApiError(res.status, message);
  }

  if (res.status === 204) {
    return undefined as T;
  }

  return (await res.json()) as T;
}
