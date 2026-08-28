"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Fragment } from "react";

import type { CampaignRole } from "@/types/campaign";

interface NavItem {
  label: string;
  href: (campaignId: string) => string;
  /** Sections not built yet (Fases 2-4) render disabled instead of linking to an empty stub. */
  implemented: boolean;
  /** DM-only sections (e.g. Diário) are hidden outright for players — never shown disabled. */
  dmOnly?: boolean;
  /** Renders a divider above this item, setting it apart as an admin action (e.g. Configurações). */
  separatorBefore?: boolean;
}

const NAV_ITEMS: NavItem[] = [
  { label: "Dashboard", href: (id) => `/campaigns/${id}`, implemented: true },
  {
    label: "Personagens",
    href: (id) => `/campaigns/${id}/characters`,
    implemented: true,
  },
  {
    label: "Catálogo",
    href: (id) => `/campaigns/${id}/catalog`,
    implemented: true,
  },
  {
    label: "Sessões",
    href: (id) => `/campaigns/${id}/sessions`,
    implemented: true,
  },
  {
    label: "World",
    href: (id) => `/campaigns/${id}/world`,
    implemented: true,
  },
  {
    label: "Inventário",
    href: (id) => `/campaigns/${id}/inventory`,
    implemented: true,
  },
  {
    label: "Handouts",
    href: (id) => `/campaigns/${id}/handouts`,
    implemented: true,
  },
  {
    label: "Diário",
    href: (id) => `/campaigns/${id}/journal`,
    implemented: true,
    dmOnly: true,
  },
  {
    label: "Recap",
    href: (id) => `/campaigns/${id}/recap`,
    implemented: true,
  },
  {
    label: "Timeline",
    href: (id) => `/campaigns/${id}/timeline`,
    implemented: true,
  },
  {
    label: "Wiki",
    href: (id) => `/campaigns/${id}/wiki`,
    implemented: true,
  },
  {
    label: "Configurações",
    href: (id) => `/campaigns/${id}/settings`,
    implemented: true,
    dmOnly: true,
    separatorBefore: true,
  },
];

export function CampaignSidebar({
  campaignId,
  role,
}: {
  campaignId: string;
  role?: CampaignRole;
}) {
  const pathname = usePathname();
  const items = NAV_ITEMS.filter((item) => !item.dmOnly || role === "dm");

  return (
    <nav
      aria-label="Navegação da campanha"
      className="hidden w-56 shrink-0 flex-col gap-1 border-r border-border bg-card p-4 md:flex"
    >
      {items.map((item) => {
        const href = item.href(campaignId);
        const active = pathname === href || pathname.startsWith(`${href}/`);
        const separator = item.separatorBefore ? (
          <div
            key={`${item.label}-separator`}
            role="separator"
            className="my-1 border-t border-border"
          />
        ) : null;

        if (!item.implemented) {
          return (
            <Fragment key={item.label}>
              {separator}
              <span
                title="Em breve"
                className="cursor-not-allowed rounded-md px-3 py-2 text-sm text-muted-foreground/50"
              >
                {item.label}
              </span>
            </Fragment>
          );
        }

        return (
          <Fragment key={item.label}>
            {separator}
            <Link
              href={href}
              className={`rounded-md px-3 py-2 text-sm transition-colors ${
                active
                  ? "bg-secondary font-medium text-secondary-foreground"
                  : "text-muted-foreground hover:bg-secondary/50"
              }`}
            >
              {item.label}
            </Link>
          </Fragment>
        );
      })}
    </nav>
  );
}

export { NAV_ITEMS };
