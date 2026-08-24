import { apiFetch } from "@/lib/api/client";
import type {
  TimelineEntry,
  TimelineEvent,
  TimelineEventCreate,
  TimelineEventUpdate,
} from "@/types/timeline";

/** Calls the timeline endpoints exposed by backend/app/timeline/router.py. */

/** A campaign's timeline: automatic session entries plus manual events, fused. */
export function getTimeline(campaignId: string): Promise<TimelineEntry[]> {
  return apiFetch<TimelineEntry[]>(`/campaigns/${campaignId}/timeline`);
}

/** Create a manual timeline event. DM-only. */
export function createTimelineEvent(
  campaignId: string,
  data: TimelineEventCreate,
): Promise<TimelineEvent> {
  return apiFetch<TimelineEvent>(`/campaigns/${campaignId}/timeline`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/** Update a manual timeline event. DM-only. */
export function updateTimelineEvent(
  eventId: string,
  data: TimelineEventUpdate,
): Promise<TimelineEvent> {
  return apiFetch<TimelineEvent>(`/timeline/${eventId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

/** Delete a manual timeline event. DM-only. */
export function deleteTimelineEvent(eventId: string): Promise<void> {
  return apiFetch<void>(`/timeline/${eventId}`, { method: "DELETE" });
}
