"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { LocaleSwitcher } from "@/components/catalog/locale-switcher";
import { getCurrentUser, logout } from "@/lib/auth/session";
import type { CampaignRole } from "@/types/campaign";

const ROLE_LABELS: Record<CampaignRole, string> = {
  dm: "Mestre",
  player: "Jogador",
};

export function Header({
  campaignName,
  role,
}: {
  campaignName: string;
  role: CampaignRole;
}) {
  const router = useRouter();
  const { data: user } = useQuery({
    queryKey: ["auth", "me"],
    queryFn: getCurrentUser,
  });

  async function handleLogout() {
    await logout();
    router.push("/auth/login");
  }

  return (
    <header className="flex items-center justify-between gap-4 border-b border-border bg-card px-4 py-3">
      <div className="min-w-0">
        <Link
          href="/campaigns"
          className="font-mono text-xs uppercase tracking-[0.2em] text-primary"
        >
          Anahita
        </Link>
        <p className="truncate font-semibold">{campaignName}</p>
      </div>

      <div className="flex shrink-0 items-center gap-3 text-sm">
        <span className="rounded-full border border-border px-2 py-0.5 text-xs text-muted-foreground">
          {ROLE_LABELS[role]}
        </span>
        <LocaleSwitcher />
        {user ? (
          <span className="hidden text-muted-foreground sm:inline">
            {user.username}
          </span>
        ) : null}
        <button
          type="button"
          onClick={handleLogout}
          className="text-muted-foreground underline-offset-2 hover:underline"
        >
          Sair
        </button>
      </div>
    </header>
  );
}
