"use client";

import { useParams } from "next/navigation";

import { CampaignSidebar } from "@/components/layout/campaign-sidebar";
import { Header } from "@/components/layout/header";
import { MobileNav } from "@/components/layout/mobile-nav";
import { useCampaign, useMyMembership } from "@/hooks/use-campaign";

export default function CampaignLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { campaignId } = useParams<{ campaignId: string }>();
  const { data: campaign } = useCampaign(campaignId);
  const { data: membership } = useMyMembership(campaignId);

  return (
    <div className="flex min-h-screen flex-col">
      <Header campaignName={campaign?.name ?? "Carregando…"} role={membership?.role ?? "player"} />
      <div className="flex flex-1">
        <CampaignSidebar campaignId={campaignId} />
        <div className="flex-1 pb-16 md:pb-0">{children}</div>
      </div>
      <MobileNav campaignId={campaignId} />
    </div>
  );
}
