/**
 * Mirrors backend/app/campaigns/schemas.py and domain.py.
 * Keep in sync manually — no codegen yet (PRD frontend backlog Fase 0).
 */

import type { HandoutType } from "@/types/handout";
import type { GameSession } from "@/types/session";
import type { Location, Npc } from "@/types/world";

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

/** A pending (unrevealed) handout, as summarized on the dashboard — DM-only. */
export interface DashboardHandout {
  id: string;
  title: string;
  handout_type: HandoutType;
  created_at: string;
}

/**
 * Cross-domain dashboard summary for a campaign, shaped by the requester's
 * role — a player always gets an empty `pending_handouts`/count (mirrors
 * backend/app/campaigns/schemas.py::CampaignDashboardRead).
 */
export interface CampaignDashboard {
  next_session: GameSession | null;
  recent_npcs: Npc[];
  recent_locations: Location[];
  pending_handouts: DashboardHandout[];
  pending_handouts_count: number;
}
