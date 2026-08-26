"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  createCampaign,
  createInvite,
  getCampaign,
  getCampaignDashboard,
  getMyMembership,
  listCampaigns,
  listMembers,
  redeemInvite,
  updateCampaign,
} from "@/lib/api/campaigns";
import type {
  CampaignCreate,
  CampaignInviteCreate,
  CampaignUpdate,
} from "@/types/campaign";

export const CAMPAIGNS_QUERY_KEY = ["campaigns"] as const;

/** List every campaign the authenticated user belongs to. */
export function useCampaigns() {
  return useQuery({
    queryKey: CAMPAIGNS_QUERY_KEY,
    queryFn: listCampaigns,
  });
}

/** A single campaign's detail. */
export function useCampaign(campaignId: string) {
  return useQuery({
    queryKey: [...CAMPAIGNS_QUERY_KEY, campaignId],
    queryFn: () => getCampaign(campaignId),
    enabled: Boolean(campaignId),
  });
}

/** The authenticated user's own role/membership in a campaign. */
export function useMyMembership(campaignId: string) {
  return useQuery({
    queryKey: [...CAMPAIGNS_QUERY_KEY, campaignId, "members", "me"],
    queryFn: () => getMyMembership(campaignId),
    enabled: Boolean(campaignId),
  });
}

/** A campaign's dashboard summary (next session, recent NPCs/locations, handouts). */
export function useCampaignDashboard(campaignId: string) {
  return useQuery({
    queryKey: [...CAMPAIGNS_QUERY_KEY, campaignId, "dashboard"],
    queryFn: () => getCampaignDashboard(campaignId),
    enabled: Boolean(campaignId),
  });
}

/** Every member of a campaign (DM and players). */
export function useMembers(campaignId: string) {
  return useQuery({
    queryKey: [...CAMPAIGNS_QUERY_KEY, campaignId, "members"],
    queryFn: () => listMembers(campaignId),
    enabled: Boolean(campaignId),
  });
}

/** Create a campaign; invalidates the campaigns list on success. */
export function useCreateCampaign() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: CampaignCreate) => createCampaign(data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: CAMPAIGNS_QUERY_KEY });
    },
  });
}

/** Update a campaign's general settings (DM only); invalidates its detail on success. */
export function useUpdateCampaign(campaignId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: CampaignUpdate) => updateCampaign(campaignId, data),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: [...CAMPAIGNS_QUERY_KEY, campaignId],
      });
    },
  });
}

/** Generate an invite for a campaign (DM only). */
export function useCreateInvite(campaignId: string) {
  return useMutation({
    mutationFn: (data: CampaignInviteCreate = {}) =>
      createInvite(campaignId, data),
  });
}

/** Redeem an invite code; invalidates the campaigns list on success. */
export function useRedeemInvite() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (inviteCode: string) => redeemInvite(inviteCode),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: CAMPAIGNS_QUERY_KEY });
    },
  });
}
