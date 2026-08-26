"use client";

import Link from "next/link";
import { useParams } from "next/navigation";

import { SessionCard } from "@/components/sessions/session-card";
import { useCampaign, useCampaignDashboard, useMyMembership } from "@/hooks/use-campaign";
import { useCharacters } from "@/hooks/use-character";
import type { HandoutType } from "@/types/handout";

const HANDOUT_TYPE_LABEL: Record<HandoutType, string> = {
  text: "Texto",
  image: "Imagem",
  map: "Mapa",
};

export default function CampaignDashboardPage() {
  const { campaignId } = useParams<{ campaignId: string }>();
  const { data: campaign, isLoading } = useCampaign(campaignId);
  const { data: membership } = useMyMembership(campaignId);
  const { data: characters } = useCharacters(campaignId);
  const { data: dashboard, isLoading: isDashboardLoading } =
    useCampaignDashboard(campaignId);
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
          {isDashboardLoading ? (
            <p className="mt-2 text-sm text-muted-foreground">Carregando…</p>
          ) : dashboard?.next_session ? (
            <div className="mt-2">
              <SessionCard campaignId={campaignId} session={dashboard.next_session} />
            </div>
          ) : (
            <p className="mt-2 text-sm text-muted-foreground">
              Nenhuma sessão futura agendada.
            </p>
          )}
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
              {isDashboardLoading ? (
                <p className="mt-2 text-sm text-muted-foreground">Carregando…</p>
              ) : dashboard &&
                (dashboard.recent_npcs.length > 0 ||
                  dashboard.recent_locations.length > 0) ? (
                <ul className="mt-2 space-y-1 text-sm">
                  {dashboard.recent_npcs.map((npc) => (
                    <li key={npc.id}>
                      <Link
                        href={`/campaigns/${campaignId}/world/npcs/${npc.id}`}
                        className="text-primary underline"
                      >
                        {npc.name}
                      </Link>
                      <span className="text-muted-foreground"> · NPC</span>
                    </li>
                  ))}
                  {dashboard.recent_locations.map((location) => (
                    <li key={location.id}>
                      <Link
                        href={`/campaigns/${campaignId}/world/locations/${location.id}`}
                        className="text-primary underline"
                      >
                        {location.name}
                      </Link>
                      <span className="text-muted-foreground"> · local</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="mt-2 text-sm text-muted-foreground">
                  Nada registrado ainda.
                </p>
              )}
            </section>

            <section className="rounded-lg border border-border bg-card p-4">
              <h2 className="font-semibold">Handouts pendentes</h2>
              {isDashboardLoading ? (
                <p className="mt-2 text-sm text-muted-foreground">Carregando…</p>
              ) : dashboard && dashboard.pending_handouts_count > 0 ? (
                <>
                  <p className="mt-2 text-sm text-muted-foreground">
                    {dashboard.pending_handouts_count} não revelado(s)
                  </p>
                  <ul className="mt-1 space-y-1 text-sm">
                    {dashboard.pending_handouts.map((handout) => (
                      <li key={handout.id}>
                        {handout.title}
                        <span className="text-muted-foreground">
                          {" "}
                          · {HANDOUT_TYPE_LABEL[handout.handout_type]}
                        </span>
                      </li>
                    ))}
                  </ul>
                  <Link
                    href={`/campaigns/${campaignId}/handouts`}
                    className="mt-2 inline-block text-sm text-primary underline"
                  >
                    Ver handouts
                  </Link>
                </>
              ) : (
                <p className="mt-2 text-sm text-muted-foreground">
                  Nenhum handout pendente.
                </p>
              )}
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
