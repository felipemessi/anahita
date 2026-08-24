"use client";

import { useDeleteTimelineEvent } from "@/hooks/use-timeline";
import type { TimelineEntry } from "@/types/timeline";

/**
 * One timeline entry. Automatic (session-derived) entries are visually
 * distinct from manual ones and can never be edited/deleted here — only
 * the DM sees a delete action, and only for manual entries.
 */
export function TimelineEventCard({
  campaignId,
  entry,
  isDm,
}: {
  campaignId: string;
  entry: TimelineEntry;
  isDm: boolean;
}) {
  const deleteEvent = useDeleteTimelineEvent(campaignId);
  const isAutomatic = entry.entry_type === "session";

  return (
    <article
      className={`space-y-1 rounded-lg border p-4 ${
        isAutomatic
          ? "border-border bg-card"
          : "border-primary/40 bg-secondary/20"
      }`}
    >
      <header className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="rounded-full border border-border px-2 py-0.5 text-xs text-muted-foreground">
            {isAutomatic ? "Sessão" : "Marco"}
          </span>
          <p className="font-medium">{entry.title}</p>
        </div>
        {isDm && !isAutomatic ? (
          <button
            type="button"
            onClick={() => deleteEvent.mutate(entry.id)}
            className="shrink-0 text-xs text-destructive underline hover:no-underline"
          >
            Apagar
          </button>
        ) : null}
      </header>
      {entry.in_game_date ? (
        <p className="text-xs text-muted-foreground">{entry.in_game_date}</p>
      ) : null}
      {entry.description ? (
        <p className="whitespace-pre-wrap text-sm">{entry.description}</p>
      ) : null}
    </article>
  );
}
