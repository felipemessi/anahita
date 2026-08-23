"use client";

import { useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";

import { useMyMembership } from "@/hooks/use-campaign";
import { useCombat } from "@/hooks/use-combat";
import { ConditionBadges } from "@/components/combat/condition-badges";
import { DamageDialog } from "@/components/combat/damage-dialog";
import { InitiativeTracker } from "@/components/combat/initiative-tracker";
import { MonsterPicker } from "@/components/combat/monster-picker";
import { TurnIndicator } from "@/components/combat/turn-indicator";
import type { EncounterParticipant } from "@/types/combat";

const STATUS_LABEL: Record<string, string> = {
  preparing: "Preparando",
  active: "Em andamento",
  completed: "Concluído",
};

export default function CombatPage() {
  const { campaignId } = useParams<{ campaignId: string }>();
  const { data: membership } = useMyMembership(campaignId);
  const isDm = membership?.role === "dm";
  const { encounter, isConnected, lastError, removeParticipant } = useCombat();
  const [showAddParticipant, setShowAddParticipant] = useState(false);

  function renderDmActions(participant: EncounterParticipant) {
    return (
      <div className="space-y-2">
        <DamageDialog participant={participant} />
        <ConditionBadges participant={participant} />
        <button
          type="button"
          onClick={() => removeParticipant(participant.id)}
          className="text-xs text-muted-foreground underline"
        >
          Remover participante
        </button>
      </div>
    );
  }

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

          <InitiativeTracker
            encounter={encounter}
            renderActions={isDm ? renderDmActions : undefined}
          />

          {isDm ? (
            <div>
              <button
                type="button"
                onClick={() => setShowAddParticipant((v) => !v)}
                className="text-sm text-primary underline"
              >
                {showAddParticipant ? "Fechar" : "Adicionar participante"}
              </button>
              {showAddParticipant ? (
                <div className="mt-2">
                  <MonsterPicker campaignId={campaignId} />
                </div>
              ) : null}
            </div>
          ) : null}

          {isDm ? <TurnIndicator /> : null}
        </>
      )}
    </main>
  );
}
