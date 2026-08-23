"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import {
  useCampaigns,
  useCreateCampaign,
  useRedeemInvite,
} from "@/hooks/use-campaign";
import { ApiError } from "@/lib/api/client";
import { getCurrentUser } from "@/lib/auth/session";
import type { CampaignStatus } from "@/types/campaign";

const STATUS_LABELS: Record<CampaignStatus, string> = {
  active: "Ativa",
  paused: "Pausada",
  archived: "Arquivada",
};

export default function CampaignsPage() {
  const router = useRouter();
  const { data: user } = useQuery({
    queryKey: ["auth", "me"],
    queryFn: getCurrentUser,
  });
  const { data: campaigns, isLoading } = useCampaigns();
  const createCampaign = useCreateCampaign();
  const redeemInvite = useRedeemInvite();

  const [name, setName] = useState("");
  const [inviteCode, setInviteCode] = useState("");
  const [inviteError, setInviteError] = useState<string | null>(null);

  async function handleCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!name.trim()) return;
    const campaign = await createCampaign.mutateAsync({ name });
    setName("");
    router.push(`/campaigns/${campaign.id}`);
  }

  async function handleRedeem(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!inviteCode.trim()) return;
    setInviteError(null);
    try {
      const membership = await redeemInvite.mutateAsync(inviteCode.trim());
      setInviteCode("");
      router.push(`/campaigns/${membership.campaign_id}`);
    } catch (err) {
      setInviteError(
        err instanceof ApiError
          ? "Código de convite inválido ou expirado."
          : "Não foi possível entrar na campanha. Tente novamente.",
      );
    }
  }

  return (
    <main className="mx-auto max-w-3xl space-y-8 px-6 py-10">
      <div>
        <h1 className="text-2xl font-bold">Minhas campanhas</h1>
        <p className="text-sm text-muted-foreground">
          Campanhas em que você participa como mestre ou jogador.
        </p>
      </div>

      <section className="space-y-3" aria-label="Lista de campanhas">
        {isLoading ? (
          <p className="text-sm text-muted-foreground">Carregando…</p>
        ) : campaigns && campaigns.length > 0 ? (
          <ul className="space-y-2">
            {campaigns.map((campaign) => (
              <li key={campaign.id}>
                <Link
                  href={`/campaigns/${campaign.id}`}
                  className="flex items-center justify-between rounded-lg border border-border bg-card px-4 py-3 transition-colors hover:bg-secondary/40"
                >
                  <div>
                    <p className="font-medium">{campaign.name}</p>
                    <p className="text-xs text-muted-foreground">
                      {user && campaign.owner_id === user.id
                        ? "Mestre"
                        : "Jogador"}{" "}
                      · {STATUS_LABELS[campaign.status]}
                    </p>
                  </div>
                  <span className="text-xs text-muted-foreground">
                    Última sessão: —
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-muted-foreground">
            Você ainda não participa de nenhuma campanha.
          </p>
        )}
      </section>

      <div className="grid gap-6 sm:grid-cols-2">
        <form
          onSubmit={handleCreate}
          className="space-y-3 rounded-lg border border-border bg-card p-4"
        >
          <h2 className="font-semibold">Criar campanha</h2>
          <label htmlFor="campaign-name" className="sr-only">
            Nome da campanha
          </label>
          <input
            id="campaign-name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Nome da campanha"
            required
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
          />
          <button
            type="submit"
            disabled={createCampaign.isPending}
            className="w-full rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-opacity hover:opacity-90 disabled:opacity-60"
          >
            {createCampaign.isPending ? "Criando…" : "Criar campanha"}
          </button>
        </form>

        <form
          onSubmit={handleRedeem}
          className="space-y-3 rounded-lg border border-border bg-card p-4"
        >
          <h2 className="font-semibold">Entrar com código de convite</h2>
          <label htmlFor="invite-code" className="sr-only">
            Código de convite
          </label>
          <input
            id="invite-code"
            value={inviteCode}
            onChange={(e) => setInviteCode(e.target.value)}
            placeholder="Código de convite"
            required
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
          />
          {inviteError ? (
            <p role="alert" className="text-sm text-destructive">
              {inviteError}
            </p>
          ) : null}
          <button
            type="submit"
            disabled={redeemInvite.isPending}
            className="w-full rounded-md border border-border px-4 py-2 text-sm font-medium transition-colors hover:bg-secondary disabled:opacity-60"
          >
            {redeemInvite.isPending ? "Entrando…" : "Entrar na campanha"}
          </button>
        </form>
      </div>
    </main>
  );
}
