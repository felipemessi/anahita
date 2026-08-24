"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  createWikiPage,
  createWikiPageLink,
  deleteWikiPage,
  deleteWikiPageLink,
  getWikiPage,
  listWikiPages,
  updateWikiPage,
} from "@/lib/api/wiki";
import type { WikiPageCreate, WikiPageLinkCreate, WikiPageUpdate } from "@/types/wiki";

export const WIKI_QUERY_KEY = ["wiki"] as const;

/** A campaign's wiki pages (summary shape). Any member. */
export function useWikiPages(campaignId: string) {
  return useQuery({
    queryKey: [...WIKI_QUERY_KEY, campaignId],
    queryFn: () => listWikiPages(campaignId),
    enabled: Boolean(campaignId),
  });
}

/** A single wiki page's full content and links. Any member. */
export function useWikiPage(pageId: string) {
  return useQuery({
    queryKey: [...WIKI_QUERY_KEY, "page", pageId],
    queryFn: () => getWikiPage(pageId),
    enabled: Boolean(pageId),
  });
}

/** Create a wiki page (DM only); invalidates the campaign's page list. */
export function useCreateWikiPage(campaignId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: WikiPageCreate) => createWikiPage(campaignId, data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [...WIKI_QUERY_KEY, campaignId] });
    },
  });
}

/** Update a wiki page (DM only); invalidates its detail and the campaign's list. */
export function useUpdateWikiPage(campaignId: string, pageId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: WikiPageUpdate) => updateWikiPage(pageId, data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [...WIKI_QUERY_KEY, "page", pageId] });
      void queryClient.invalidateQueries({ queryKey: [...WIKI_QUERY_KEY, campaignId] });
    },
  });
}

/** Delete a wiki page (DM only); invalidates the campaign's page list. */
export function useDeleteWikiPage(campaignId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (pageId: string) => deleteWikiPage(pageId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [...WIKI_QUERY_KEY, campaignId] });
    },
  });
}

/** Link a wiki page to an NPC/location/faction (DM only); invalidates its detail. */
export function useCreateWikiPageLink(pageId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: WikiPageLinkCreate) => createWikiPageLink(pageId, data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [...WIKI_QUERY_KEY, "page", pageId] });
    },
  });
}

/** Remove a wiki page link (DM only); invalidates the page's detail. */
export function useDeleteWikiPageLink(pageId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (linkId: string) => deleteWikiPageLink(pageId, linkId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [...WIKI_QUERY_KEY, "page", pageId] });
    },
  });
}
