"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { useRedeemInvite } from "@/hooks/use-campaign";
import { ApiError } from "@/lib/api/client";

/** Accepts an invite link (`/join/[inviteCode]`) and redeems it automatically. */
export default function JoinInvitePage() {
  const { inviteCode } = useParams<{ inviteCode: string }>();
  const router = useRouter();
  const redeemInvite = useRedeemInvite();
  const [error, setError] = useState<string | null>(null);
  const attempted = useRef(false);

  useEffect(() => {
    if (attempted.current) return;
    attempted.current = true;

    redeemInvite
      .mutateAsync(inviteCode)
      .then((membership) => {
        router.push(`/campaigns/${membership.campaign_id}`);
      })
      .catch((err: unknown) => {
        setError(
          err instanceof ApiError
            ? "Código de convite inválido ou expirado."
            : "Não foi possível entrar na campanha. Tente novamente.",
        );
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [inviteCode]);

  return (
    <main className="flex min-h-screen items-center justify-center px-6 text-center">
      {error ? (
        <div className="space-y-2">
          <p role="alert" className="text-destructive">
            {error}
          </p>
          <button
            type="button"
            onClick={() => router.push("/campaigns")}
            className="text-sm text-primary underline"
          >
            Voltar para minhas campanhas
          </button>
        </div>
      ) : (
        <p className="text-sm text-muted-foreground">Entrando na campanha…</p>
      )}
    </main>
  );
}
