"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  createTimelineEvent,
  deleteTimelineEvent,
  getTimeline,
  updateTimelineEvent,
} from "@/lib/api/timeline";
import type { TimelineEventCreate, TimelineEventUpdate } from "@/types/timeline";

export const TIMELINE_QUERY_KEY = ["timeline"] as const;

/** A campaign's fused timeline (automatic session entries + manual events). */
export function useTimeline(campaignId: string) {
  return useQuery({
    queryKey: [...TIMELINE_QUERY_KEY, campaignId],
    queryFn: () => getTimeline(campaignId),
    enabled: Boolean(campaignId),
  });
}

/** Create a manual timeline event (DM only); invalidates the campaign's timeline. */
export function useCreateTimelineEvent(campaignId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: TimelineEventCreate) => createTimelineEvent(campaignId, data),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: [...TIMELINE_QUERY_KEY, campaignId],
      });
    },
  });
}

/** Update a manual timeline event (DM only); invalidates the campaign's timeline. */
export function useUpdateTimelineEvent(campaignId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ eventId, data }: { eventId: string; data: TimelineEventUpdate }) =>
      updateTimelineEvent(eventId, data),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: [...TIMELINE_QUERY_KEY, campaignId],
      });
    },
  });
}

/** Delete a manual timeline event (DM only); invalidates the campaign's timeline. */
export function useDeleteTimelineEvent(campaignId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (eventId: string) => deleteTimelineEvent(eventId),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: [...TIMELINE_QUERY_KEY, campaignId],
      });
    },
  });
}
