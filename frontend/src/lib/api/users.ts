import { apiFetch } from "@/lib/api/client";
import type { SessionUser } from "@/lib/auth/session";

/**
 * Resolve public profiles for a batch of user ids (e.g. campaign member
 * names) — calls `GET /auth/users?ids=`.
 */
export function listUsersByIds(ids: string[]): Promise<SessionUser[]> {
  if (ids.length === 0) return Promise.resolve([]);
  const params = new URLSearchParams();
  for (const id of ids) params.append("ids", id);
  return apiFetch<SessionUser[]>(`/auth/users?${params.toString()}`);
}
