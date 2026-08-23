"use client";

import { useParams } from "next/navigation";
import { useState, type FormEvent } from "react";

import {
  useCampaign,
  useCreateInvite,
  useMembers,
  useMyMembership,
} from "@/hooks/use-campaign";
import type { CampaignRole } from "@/types/campaign";

const ROLE_LABELS: Record<CampaignRole, string> = {
  dm: "Mestre",
  player: "Jogador",
};

/**
 * Backend has no "update campaign" endpoint yet (name/description/setting
 * are read-only after creation) — see anahita-frontend-backlog.md Fase 1.
 * Member list and invite generation are both real.
 */
export default function CampaignSettingsPage() {
  const { campaignId } = useParams<{ campaignId: string }>();
  const { data: campaign } = useCampaign(campaignId);
  const { data: membership } = useMyMembership(campaignId);
  const { data: members } = useMembers(campaignId);
  const createInvite = useCreateInvite(campaignId);
  const [inviteRole, setInviteRole] = useState<CampaignRole>("player");
  const [generatedCode, setGeneratedCode] = useState<string | null>(null);

  const isDm = membership?.role === "dm";

  async function handleCreateInvite(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const invite = await createInvite.mutateAsync({ role: inviteRole });
    setGeneratedCode(invite.invite_code);
  }

  return (
    <main className="mx-auto max-w-2xl space-y-8 px-6 py-10">
      <div>
        <h1 className="text-2xl font-bold">Configurações da campanha</h1>
        {campaign ? (
          <p className="text-sm text-muted-foreground">{campaign.name}</p>
        ) : null}
      </div>

      <section className="space-y-2 rounded-lg border border-border bg-card p-4">
        <h2 className="font-semibold">Sua função</h2>
        <p className="text-sm text-muted-foreground">
          {membership ? ROLE_LABELS[membership.role] : "Carregando…"}
        </p>
      </section>

      <section className="space-y-3 rounded-lg border border-border bg-card p-4">
        <h2 className="font-semibold">Membros</h2>
        {members && members.length > 0 ? (
          <ul className="divide-y divide-border">
            {members.map((member) => (
              <li
                key={member.id}
                className="flex items-center justify-between py-2 text-sm"
              >
                <span className="font-mono text-xs text-muted-foreground">
                  {member.user_id}
                </span>
                <span>{ROLE_LABELS[member.role]}</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-muted-foreground">Carregando…</p>
        )}
      </section>

      {isDm ? (
        <section
          aria-label="Gestão de membros"
          className="space-y-3 rounded-lg border border-border bg-card p-4"
        >
          <h2 className="font-semibold">Gerar convite</h2>
          <form onSubmit={handleCreateInvite} className="flex items-end gap-3">
            <div className="space-y-1">
              <label htmlFor="invite-role" className="text-sm font-medium">
                Função do convidado
              </label>
              <select
                id="invite-role"
                value={inviteRole}
                onChange={(e) => setInviteRole(e.target.value as CampaignRole)}
                className="rounded-md border border-input bg-background px-2 py-1.5 text-sm"
              >
                <option value="player">Jogador</option>
                <option value="dm">Mestre</option>
              </select>
            </div>
            <button
              type="submit"
              disabled={createInvite.isPending}
              className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-opacity hover:opacity-90 disabled:opacity-60"
            >
              {createInvite.isPending ? "Gerando…" : "Gerar convite"}
            </button>
          </form>
          {generatedCode ? (
            <p className="font-mono text-sm">
              Código: <span className="font-semibold">{generatedCode}</span>
            </p>
          ) : null}
        </section>
      ) : null}
    </main>
  );
}
