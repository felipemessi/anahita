"use client";

import { useRevealHandout } from "@/hooks/use-handouts";

/** DM-only button to reveal a not-yet-revealed handout. */
export function HandoutRevealButton({
  handoutId,
  campaignId,
}: {
  handoutId: string;
  campaignId: string;
}) {
  const reveal = useRevealHandout(campaignId);

  return (
    <button
      type="button"
      onClick={() => reveal.mutate(handoutId)}
      disabled={reveal.isPending}
      className="rounded-md border border-border px-3 py-1 text-xs hover:bg-secondary/50 disabled:opacity-50"
    >
      Revelar
    </button>
  );
}
