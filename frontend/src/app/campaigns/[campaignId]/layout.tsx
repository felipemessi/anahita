"use client";

import { usePathname, useParams } from "next/navigation";

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
  const pathname = usePathname();
  const { data: campaign } = useCampaign(campaignId);
  const { data: membership } = useMyMembership(campaignId);

  // The live combat tracker (Fase 2 história 2) is fullscreen mobile-first —
  // it hides the campaign chrome instead of getting its own route segment
  // outside `[campaignId]`, since it still needs `campaignId` from this
  // layout's params.
  const isFullscreenCombat = /\/combat\/[^/]+/.test(pathname ?? "");
  if (isFullscreenCombat) {
    return <div className="min-h-screen">{children}</div>;
  }

  return (
    <div className="flex min-h-screen flex-col">
      <Header campaignName={campaign?.name ?? "Carregando…"} role={membership?.role ?? "player"} />
      <div className="flex flex-1">
        <CampaignSidebar campaignId={campaignId} role={membership?.role} />
        <div className="flex-1 pb-16 md:pb-0">{children}</div>
      </div>
      <MobileNav campaignId={campaignId} role={membership?.role} />
    </div>
  );
}
