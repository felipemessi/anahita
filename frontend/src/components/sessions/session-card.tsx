import Link from "next/link";

import type { GameSession, SessionStatus } from "@/types/session";

const STATUS_LABEL: Record<SessionStatus, string> = {
  planned: "Planejada",
  in_progress: "Em andamento",
  completed: "Concluída",
};

/** Summary card for a session, linking to its detail/notes page. */
export function SessionCard({
  campaignId,
  session,
}: {
  campaignId: string;
  session: GameSession;
}) {
  return (
    <Link
      href={`/campaigns/${campaignId}/sessions/${session.id}`}
      className="flex items-center justify-between rounded-lg border border-border bg-card px-4 py-3 transition-colors hover:bg-secondary/40"
    >
      <div>
        <p className="font-medium">
          Sessão {session.session_number} — {session.title}
        </p>
        {session.scheduled_date ? (
          <p className="text-sm text-muted-foreground">{session.scheduled_date}</p>
        ) : null}
      </div>
      <span className="rounded-full border border-border px-3 py-1 text-xs text-muted-foreground">
        {STATUS_LABEL[session.status]}
      </span>
    </Link>
  );
}
