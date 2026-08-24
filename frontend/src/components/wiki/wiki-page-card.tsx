import Link from "next/link";

import type { WikiPageSummary } from "@/types/wiki";

/** Summary card for a wiki page, linking to its detail page. */
export function WikiPageCard({
  campaignId,
  page,
}: {
  campaignId: string;
  page: WikiPageSummary;
}) {
  const tags = page.tags
    ?.split(",")
    .map((tag) => tag.trim())
    .filter(Boolean);

  return (
    <Link
      href={`/campaigns/${campaignId}/wiki/${page.id}`}
      className="flex items-center justify-between rounded-lg border border-border bg-card px-4 py-3 transition-colors hover:bg-secondary/40"
    >
      <p className="font-medium">{page.title}</p>
      {tags && tags.length > 0 ? (
        <div className="flex gap-1">
          {tags.map((tag) => (
            <span
              key={tag}
              className="rounded-full border border-border px-2 py-0.5 text-xs text-muted-foreground"
            >
              {tag}
            </span>
          ))}
        </div>
      ) : null}
    </Link>
  );
}
