"use client";

import { useParams } from "next/navigation";
import { useEffect, useState, type FormEvent } from "react";

import {
  useCampaign,
  useCreateInvite,
  useMembers,
  useMyMembership,
  useUpdateCampaign,
} from "@/hooks/use-campaign";
import { useUserProfiles } from "@/hooks/use-users";
import type { CampaignRole } from "@/types/campaign";

const ROLE_LABELS: Record<CampaignRole, string> = {
  dm: "Mestre",
  player: "Jogador",
};

export default function CampaignSettingsPage() {
  const { campaignId } = useParams<{ campaignId: string }>();
  const { data: campaign } = useCampaign(campaignId);
  const { data: membership } = useMyMembership(campaignId);
  const { data: members } = useMembers(campaignId);
  const { data: memberProfiles } = useUserProfiles(
    members?.map((m) => m.user_id) ?? [],
  );
  const createInvite = useCreateInvite(campaignId);
  const updateCampaign = useUpdateCampaign(campaignId);
  const [inviteRole, setInviteRole] = useState<CampaignRole>("player");
  const [generatedCode, setGeneratedCode] = useState<string | null>(null);

  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [setting, setSetting] = useState("");
  const [settingsError, setSettingsError] = useState<string | null>(null);
  const [settingsSaved, setSettingsSaved] = useState(false);

  useEffect(() => {
    if (!campaign) return;
    setName(campaign.name);
    setDescription(campaign.description ?? "");
    setSetting(campaign.setting ?? "");
  }, [campaign]);

  const isDm = membership?.role === "dm";

  function usernameFor(userId: string): string {
    return memberProfiles?.find((u) => u.id === userId)?.username ?? userId;
  }

  async function handleCreateInvite(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const invite = await createInvite.mutateAsync({ role: inviteRole });
    setGeneratedCode(invite.invite_code);
  }

  async function handleSaveSettings(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSettingsError(null);
    setSettingsSaved(false);
    try {
      await updateCampaign.mutateAsync({ name, description, setting });
      setSettingsSaved(true);
    } catch {
      setSettingsError("Não foi possível salvar. Tente novamente.");
    }
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
        <h2 className="font-semibold">Configurações gerais</h2>
        {isDm ? (
          <form onSubmit={handleSaveSettings} className="space-y-3">
            <div className="space-y-1">
              <label htmlFor="campaign-name" className="text-sm font-medium">
                Nome
              </label>
              <input
                id="campaign-name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              />
            </div>
            <div className="space-y-1">
              <label htmlFor="campaign-description" className="text-sm font-medium">
                Descrição
              </label>
              <textarea
                id="campaign-description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={3}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              />
            </div>
            <div className="space-y-1">
              <label htmlFor="campaign-setting" className="text-sm font-medium">
                Cenário
              </label>
              <input
                id="campaign-setting"
                value={setting}
                onChange={(e) => setSetting(e.target.value)}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              />
            </div>
            {settingsError ? (
              <p role="alert" className="text-sm text-destructive">
                {settingsError}
              </p>
            ) : null}
            {settingsSaved ? (
              <p className="text-sm text-primary">Salvo.</p>
            ) : null}
            <button
              type="submit"
              disabled={updateCampaign.isPending}
              className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-opacity hover:opacity-90 disabled:opacity-60"
            >
              {updateCampaign.isPending ? "Salvando…" : "Salvar"}
            </button>
          </form>
        ) : (
          <dl className="space-y-1 text-sm">
            <div className="flex justify-between">
              <dt className="text-muted-foreground">Nome</dt>
              <dd>{campaign?.name}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-muted-foreground">Descrição</dt>
              <dd>{campaign?.description || "—"}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-muted-foreground">Cenário</dt>
              <dd>{campaign?.setting || "—"}</dd>
            </div>
          </dl>
        )}
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
                <span>{usernameFor(member.user_id)}</span>
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
