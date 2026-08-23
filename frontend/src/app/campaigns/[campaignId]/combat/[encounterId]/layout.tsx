"use client";

import { useParams } from "next/navigation";

import { CombatProvider } from "@/providers/combat-provider";

/**
 * Fullscreen mobile-first shell for the live combat tracker — the campaign
 * chrome (header/sidebar/mobile-nav) is hidden by the parent
 * `[campaignId]/layout.tsx` for this route.
 */
export default function CombatLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { encounterId } = useParams<{ encounterId: string }>();

  return (
    <CombatProvider encounterId={encounterId}>
      <div className="flex min-h-screen flex-col bg-background">{children}</div>
    </CombatProvider>
  );
}
