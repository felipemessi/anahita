"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { NAV_ITEMS } from "@/components/layout/campaign-sidebar";
import type { CampaignRole } from "@/types/campaign";

/**
 * Hamburger button that opens the app's general navigation (the same
 * items as `CampaignSidebar`/`MobileNav`) as a dismissible overlay panel,
 * rather than permanent chrome — for pages like the character ficha
 * (Fase 10) that want the full width for their own content and only need
 * occasional access to the rest of the app.
 */
export function AppNavMenu({
  campaignId,
  role,
}: {
  campaignId: string;
  role?: CampaignRole;
}) {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const items = NAV_ITEMS.filter(
    (item) => item.implemented && (!item.dmOnly || role === "dm"),
  );

  useEffect(() => {
    if (!open) return;

    function handlePointerDown(event: MouseEvent) {
      if (!containerRef.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    }
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") setOpen(false);
    }

    document.addEventListener("mousedown", handlePointerDown);
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("mousedown", handlePointerDown);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [open]);

  return (
    <div ref={containerRef} className="relative">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        aria-haspopup="true"
        aria-label="Abrir navegação"
        className="flex h-9 w-9 flex-col items-center justify-center gap-1 rounded-md border border-border hover:bg-secondary"
      >
        <span aria-hidden="true" className="block h-0.5 w-4 bg-foreground" />
        <span aria-hidden="true" className="block h-0.5 w-4 bg-foreground" />
        <span aria-hidden="true" className="block h-0.5 w-4 bg-foreground" />
      </button>

      {open ? (
        <>
          {/* Backdrop: closes the menu on click, but is absolutely
              positioned so it never displaces the ficha's own content. */}
          <div
            aria-hidden="true"
            className="fixed inset-0 z-20 bg-background/50"
            onClick={() => setOpen(false)}
          />
          <nav
            aria-label="Navegação geral"
            className="absolute left-0 z-30 mt-1 w-56 rounded-lg border border-border bg-card p-1 shadow-lg"
          >
            {items.map((item) => {
              const href = item.href(campaignId);
              const active = pathname === href || pathname.startsWith(`${href}/`);
              return (
                <Link
                  key={item.label}
                  href={href}
                  onClick={() => setOpen(false)}
                  className={`block rounded-md px-3 py-2 text-sm transition-colors ${
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
        </>
      ) : null}
    </div>
  );
}
