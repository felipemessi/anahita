"use client";

import Link from "next/link";
import { useParams } from "next/navigation";

import { useMyMembership } from "@/hooks/use-campaign";
import { useCombat } from "@/hooks/use-combat";
import { InitiativeTracker } from "@/components/combat/initiative-tracker";

const STATUS_LABEL: Record<string, string> = {
  preparing: "Preparando",
  active: "Em andamento",
  completed: "Concluído",
};

export default function CombatPage() {
  const { campaignId } = useParams<{ campaignId: string }>();
  const { data: membership } = useMyMembership(campaignId);
  const isDm = membership?.role === "dm";
  const { encounter, isConnected, lastError, advanceTurn } = useCombat();

  return (
    <main className="mx-auto flex w-full max-w-lg flex-1 flex-col gap-4 px-4 py-4">
      <div className="flex items-center justify-between">
        <Link
          href={`/campaigns/${campaignId}/sessions`}
          className="text-sm text-muted-foreground underline"
        >
          ← Sessões
        </Link>
        <span
          className={`text-xs ${isConnected ? "text-emerald-500" : "text-muted-foreground"}`}
        >
          {isConnected ? "Conectado" : "Conectando…"}
        </span>
      </div>

      {!encounter ? (
        <p className="text-sm text-muted-foreground">Sincronizando combate…</p>
      ) : (
        <>
          <div>
            <h1 className="text-xl font-bold">{encounter.name}</h1>
            <p className="text-sm text-muted-foreground">
              {STATUS_LABEL[encounter.status] ?? encounter.status} · Round{" "}
              {encounter.current_round}
            </p>
          </div>

          {lastError ? (
            <p role="alert" className="text-sm text-destructive">
              {lastError}
            </p>
          ) : null}

          <InitiativeTracker encounter={encounter} />

          {isDm && encounter.status === "active" ? (
            <button
              type="button"
              onClick={advanceTurn}
              className="sticky bottom-4 mt-auto rounded-md bg-primary px-4 py-3 text-sm font-medium text-primary-foreground hover:opacity-90"
            >
              Avançar turno
            </button>
          ) : null}
        </>
      )}
    </main>
  );
}
