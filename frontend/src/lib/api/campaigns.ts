import { apiFetch } from "@/lib/api/client";
import type {
  Campaign,
  CampaignCreate,
  CampaignInvite,
  CampaignInviteCreate,
  CampaignMember,
  CampaignUpdate,
} from "@/types/campaign";

/** Calls the campaigns endpoints exposed by backend/app/campaigns/router.py. */

/** List every campaign the authenticated user belongs to. */
export function listCampaigns(): Promise<Campaign[]> {
  return apiFetch<Campaign[]>("/campaigns");
}

/** Create a campaign; the authenticated user becomes its DM. */
export function createCampaign(data: CampaignCreate): Promise<Campaign> {
  return apiFetch<Campaign>("/campaigns", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/** Get a campaign's detail. Viewable by any of its members. */
export function getCampaign(campaignId: string): Promise<Campaign> {
  return apiFetch<Campaign>(`/campaigns/${campaignId}`);
}

/** Update a campaign's general settings; only the campaign's DM may do this. */
export function updateCampaign(
  campaignId: string,
  data: CampaignUpdate,
): Promise<Campaign> {
  return apiFetch<Campaign>(`/campaigns/${campaignId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

/** Get the authenticated user's own membership (id + role) in a campaign. */
export function getMyMembership(campaignId: string): Promise<CampaignMember> {
  return apiFetch<CampaignMember>(`/campaigns/${campaignId}/members/me`);
}

/** List every member of a campaign. Viewable by any of its members. */
export function listMembers(campaignId: string): Promise<CampaignMember[]> {
  return apiFetch<CampaignMember[]>(`/campaigns/${campaignId}/members`);
}

/** Generate an invite for a campaign; only the campaign's DM may do this. */
export function createInvite(
  campaignId: string,
  data: CampaignInviteCreate = {},
): Promise<CampaignInvite> {
  return apiFetch<CampaignInvite>(`/campaigns/${campaignId}/invites`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/** Redeem an invite code, joining the campaign with the invite's role. */
export function redeemInvite(inviteCode: string): Promise<CampaignMember> {
  return apiFetch<CampaignMember>("/campaigns/invites/redeem", {
    method: "POST",
    body: JSON.stringify({ invite_code: inviteCode }),
  });
}
