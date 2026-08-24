import { apiFetch } from "@/lib/api/client";
import type { Handout, HandoutCreateFields } from "@/types/handout";

/** Calls the handout endpoints exposed by backend/app/handouts/router.py. */

/** List a campaign's handouts. Non-DM members only see revealed ones (server-filtered). */
export function listHandouts(campaignId: string): Promise<Handout[]> {
  return apiFetch<Handout[]>(`/campaigns/${campaignId}/handouts`);
}

/**
 * Create a handout, optionally uploading a file. DM only.
 *
 * Sent as `multipart/form-data` (not JSON) so the image/map file can ride
 * along in the same request — see backend/app/handouts/router.py.
 */
export function createHandout(
  campaignId: string,
  fields: HandoutCreateFields,
  file?: File | null,
): Promise<Handout> {
  const form = new FormData();
  form.append("title", fields.title);
  form.append("handout_type", fields.handout_type);
  if (fields.content) form.append("content", fields.content);
  if (fields.session_id) form.append("session_id", fields.session_id);
  if (file) form.append("file", file);

  return apiFetch<Handout>(`/campaigns/${campaignId}/handouts`, {
    method: "POST",
    body: form,
  });
}

/** Reveal a handout, broadcasting to any active encounter's session (PRD §10.3). DM only. */
export function revealHandout(handoutId: string): Promise<Handout> {
  return apiFetch<Handout>(`/handouts/${handoutId}/reveal`, { method: "POST" });
}
