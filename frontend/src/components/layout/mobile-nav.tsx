"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { NAV_ITEMS } from "@/components/layout/campaign-sidebar";
import type { CampaignRole } from "@/types/campaign";

/** Bottom tab bar shown on small screens instead of the desktop sidebar. */
export function MobileNav({
  campaignId,
  role,
}: {
  campaignId: string;
  role?: CampaignRole;
}) {
  const pathname = usePathname();
  const implementedItems = NAV_ITEMS.filter(
    (item) => item.implemented && (!item.dmOnly || role === "dm"),
  );

  return (
    <nav
      aria-label="Navegação da campanha"
      className="fixed inset-x-0 bottom-0 z-10 flex justify-around border-t border-border bg-card py-2 md:hidden"
    >
      {implementedItems.map((item) => {
        const href = item.href(campaignId);
        const active = pathname === href || pathname.startsWith(`${href}/`);

        return (
          <Link
            key={item.label}
            href={href}
            className={`px-2 py-1 text-xs ${
              active ? "font-medium text-primary" : "text-muted-foreground"
            }`}
          >
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
