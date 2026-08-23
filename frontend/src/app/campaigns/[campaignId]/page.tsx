"use client";

import Link from "next/link";
import { useParams } from "next/navigation";

import { useCampaign, useMyMembership } from "@/hooks/use-campaign";
import { useCharacters } from "@/hooks/use-character";

/**
 * Backend has no sessions endpoints yet (Fase 2), so "próxima sessão" and
 * "atividade recente" render as placeholders until that domain exists.
 */
export default function CampaignDashboardPage() {
  const { campaignId } = useParams<{ campaignId: string }>();
  const { data: campaign, isLoading } = useCampaign(campaignId);
  const { data: membership } = useMyMembership(campaignId);
  const { data: characters } = useCharacters(campaignId);
  const isDm = membership?.role === "dm";

  if (isLoading) {
    return <p className="p-6 text-sm text-muted-foreground">Carregando…</p>;
  }

  if (!campaign) {
    return <p className="p-6 text-sm text-muted-foreground">Campanha não encontrada.</p>;
  }

  return (
    <main className="mx-auto max-w-4xl space-y-8 px-6 py-10">
      <div>
        <h1 className="text-2xl font-bold">{campaign.name}</h1>
        {campaign.description ? (
          <p className="text-sm text-muted-foreground">{campaign.description}</p>
        ) : null}
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <section className="rounded-lg border border-border bg-card p-4">
          <h2 className="font-semibold">Próxima sessão</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            Em breve (aguardando backend de sessões).
          </p>
        </section>

        <section className="rounded-lg border border-border bg-card p-4">
          <h2 className="font-semibold">Personagens ativos</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            {characters ? `${characters.length} personagem(ns)` : "Carregando…"}
          </p>
          <Link
            href={`/campaigns/${campaignId}/characters`}
            className="mt-2 inline-block text-sm text-primary underline"
          >
            Ver personagens
          </Link>
        </section>

        {isDm ? (
          <>
            <section className="rounded-lg border border-border bg-card p-4">
              <h2 className="font-semibold">NPCs e locais recentes</h2>
              <p className="mt-2 text-sm text-muted-foreground">
                Em breve (aguardando backend de world-building).
              </p>
            </section>

            <section className="rounded-lg border border-border bg-card p-4">
              <h2 className="font-semibold">Handouts pendentes</h2>
              <p className="mt-2 text-sm text-muted-foreground">
                Em breve (aguardando backend de handouts).
              </p>
            </section>
          </>
        ) : null}
      </div>

      <div className="flex gap-3 text-sm">
        <Link
          href={`/campaigns/${campaignId}/catalog`}
          className="rounded-md border border-border px-4 py-2 hover:bg-secondary"
        >
          Catálogo
        </Link>
        {isDm ? (
          <Link
            href={`/campaigns/${campaignId}/settings`}
            className="rounded-md border border-border px-4 py-2 hover:bg-secondary"
          >
            Configurações
          </Link>
        ) : null}
      </div>
    </main>
  );
}
