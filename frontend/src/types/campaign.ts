/**
 * Mirrors backend/app/campaigns/schemas.py and domain.py.
 * Keep in sync manually — no codegen yet (PRD frontend backlog Fase 0).
 */

export type CampaignStatus = "active" | "paused" | "archived";

export type CampaignRole = "dm" | "player";

export interface Campaign {
  id: string;
  name: string;
  description: string | null;
  setting: string | null;
  owner_id: string;
  status: CampaignStatus;
  created_at: string;
}

export interface CampaignCreate {
  name: string;
  description?: string | null;
  setting?: string | null;
}

export interface CampaignUpdate {
  name?: string;
  description?: string;
  setting?: string;
}

export interface CampaignMember {
  id: string;
  campaign_id: string;
  user_id: string;
  role: CampaignRole;
  joined_at: string;
}

export interface CampaignInvite {
  id: string;
  campaign_id: string;
  invite_code: string;
  role: CampaignRole;
  expires_at: string;
  used_by: string | null;
}

export interface CampaignInviteCreate {
  role?: CampaignRole;
  expires_in_hours?: number;
}

export interface CampaignInviteRedeem {
  invite_code: string;
}
