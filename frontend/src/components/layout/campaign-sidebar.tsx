"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

interface NavItem {
  label: string;
  href: (campaignId: string) => string;
  /** Sections not built yet (Fases 2-4) render disabled instead of linking to an empty stub. */
  implemented: boolean;
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
    implemented: false,
  },
  {
    label: "World",
    href: (id) => `/campaigns/${id}/world`,
    implemented: false,
  },
  {
    label: "Inventário",
    href: (id) => `/campaigns/${id}/inventory`,
    implemented: false,
  },
  {
    label: "Handouts",
    href: (id) => `/campaigns/${id}/handouts`,
    implemented: false,
  },
  {
    label: "Configurações",
    href: (id) => `/campaigns/${id}/settings`,
    implemented: true,
  },
];

export function CampaignSidebar({ campaignId }: { campaignId: string }) {
  const pathname = usePathname();

  return (
    <nav
      aria-label="Navegação da campanha"
      className="hidden w-56 shrink-0 flex-col gap-1 border-r border-border bg-card p-4 md:flex"
    >
      {NAV_ITEMS.map((item) => {
        const href = item.href(campaignId);
        const active = pathname === href || pathname.startsWith(`${href}/`);

        if (!item.implemented) {
          return (
            <span
              key={item.label}
              title="Em breve"
              className="cursor-not-allowed rounded-md px-3 py-2 text-sm text-muted-foreground/50"
            >
              {item.label}
            </span>
          );
        }

        return (
          <Link
            key={item.label}
            href={href}
            className={`rounded-md px-3 py-2 text-sm transition-colors ${
              active
                ? "bg-secondary font-medium text-secondary-foreground"
                : "text-muted-foreground hover:bg-secondary/50"
            }`}
          >
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}

export { NAV_ITEMS };
