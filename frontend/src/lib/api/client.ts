"use client";

/**
 * Client-side API client. Keeps the access token in memory only (never
 * localStorage, to limit XSS exposure) and transparently refreshes it via
 * the httpOnly refresh-token cookie on a 401 response.
 *
 * See docs/anahita-frontend-prd.md §4.3.
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "/api";

let accessToken: string | null = null;

/** Store the current access token (or clear it by passing null). */
export function setAccessToken(token: string | null): void {
  accessToken = token;
}

/** Read the current in-memory access token. */
export function getAccessToken(): string | null {
  return accessToken;
}

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
    /**
     * The raw `detail` field of the error response body — usually the
     * same string as `message`, but some endpoints send a structured
     * object instead (e.g. level-up's `requires_choice` 422). Callers that
     * need the structured shape should narrow this themselves.
     */
    public readonly detail?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

let refreshPromise: Promise<string | null> | null = null;

/**
 * Calls POST /auth/refresh using the httpOnly refresh cookie. De-duplicates
 * concurrent refresh attempts behind a single in-flight promise.
 */
async function refreshAccessToken(): Promise<string | null> {
  if (!refreshPromise) {
    refreshPromise = fetch(`${API_BASE_URL}/auth/refresh`, {
      method: "POST",
      credentials: "include",
    })
      .then(async (res) => {
        if (!res.ok) {
          setAccessToken(null);
          return null;
        }
        const data = (await res.json()) as { access_token: string };
        setAccessToken(data.access_token);
        return data.access_token;
      })
      .catch(() => {
        setAccessToken(null);
        return null;
      })
      .finally(() => {
        refreshPromise = null;
      });
  }
  return refreshPromise;
}

export interface ApiFetchOptions extends RequestInit {
  /** Skip the automatic refresh-and-retry on 401 (used by auth endpoints themselves). */
  skipAuthRefresh?: boolean;
  /** Catalog locale (`en`, `pt-BR`, …) to append as `?locale=` — see lib/api/catalog.ts. */
  locale?: string;
}

/**
 * Authenticated fetch wrapper for the backend API. Attaches the in-memory
 * access token, retries once after a transparent refresh on 401, and throws
 * `ApiError` for non-2xx responses.
 */
export async function apiFetch<T>(
  path: string,
  { skipAuthRefresh, locale, ...init }: ApiFetchOptions = {},
): Promise<T> {
  const url = locale
    ? `${path}${path.includes("?") ? "&" : "?"}locale=${encodeURIComponent(locale)}`
    : path;

  // A FormData body (multipart file upload, e.g. handout creation) must not
  // get a manual Content-Type — the browser sets one with the right
  // boundary. Omitting it here is the only way to get that behavior.
  const isFormData = init.body instanceof FormData;

  const request = () =>
    fetch(`${API_BASE_URL}${url}`, {
      ...init,
      credentials: "include",
      headers: {
        ...(isFormData ? {} : { "Content-Type": "application/json" }),
        ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
        ...init.headers,
      },
    });

  let response = await request();

  if (response.status === 401 && !skipAuthRefresh) {
    const newToken = await refreshAccessToken();
    if (newToken) {
      response = await request();
    }
  }

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const detail = (body as { detail?: unknown } | null)?.detail;
    const message = typeof detail === "string" ? detail : response.statusText;
    throw new ApiError(response.status, message, detail);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}
