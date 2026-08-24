import { apiFetch } from "@/lib/api/client";
import type {
  WikiPage,
  WikiPageCreate,
  WikiPageLink,
  WikiPageLinkCreate,
  WikiPageSummary,
  WikiPageUpdate,
} from "@/types/wiki";

/** Calls the wiki endpoints exposed by backend/app/wiki/router.py. */

/** List a campaign's wiki pages (id/title/tags only). Any member. */
export function listWikiPages(campaignId: string): Promise<WikiPageSummary[]> {
  return apiFetch<WikiPageSummary[]>(`/campaigns/${campaignId}/wiki`);
}

/** Fetch a wiki page's full content and its links. Any member. */
export function getWikiPage(pageId: string): Promise<WikiPage> {
  return apiFetch<WikiPage>(`/wiki/${pageId}`);
}

/** Create a wiki page; `slug` is derived server-side from `title`. DM-only. */
export function createWikiPage(
  campaignId: string,
  data: WikiPageCreate,
): Promise<WikiPage> {
  return apiFetch<WikiPage>(`/campaigns/${campaignId}/wiki`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/** Update a wiki page's title/content/tags. DM-only. */
export function updateWikiPage(
  pageId: string,
  data: WikiPageUpdate,
): Promise<WikiPage> {
  return apiFetch<WikiPage>(`/wiki/${pageId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

/** Delete a wiki page and its links. DM-only. */
export function deleteWikiPage(pageId: string): Promise<void> {
  return apiFetch<void>(`/wiki/${pageId}`, { method: "DELETE" });
}

/** Link a wiki page to an NPC, location, or faction. DM-only. */
export function createWikiPageLink(
  pageId: string,
  data: WikiPageLinkCreate,
): Promise<WikiPageLink> {
  return apiFetch<WikiPageLink>(`/wiki/${pageId}/links`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/** Remove a wiki page link. DM-only. */
export function deleteWikiPageLink(pageId: string, linkId: string): Promise<void> {
  return apiFetch<void>(`/wiki/${pageId}/links/${linkId}`, { method: "DELETE" });
}
