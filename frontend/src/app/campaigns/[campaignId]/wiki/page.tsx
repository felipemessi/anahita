"use client";

import { useParams } from "next/navigation";

import { WikiPageCard } from "@/components/wiki/wiki-page-card";
import { WikiPageEditor } from "@/components/wiki/wiki-page-editor";
import { useMyMembership } from "@/hooks/use-campaign";
import { useWikiPages } from "@/hooks/use-wiki";

export default function WikiPage() {
  const { campaignId } = useParams<{ campaignId: string }>();
  const { data: pages, isLoading } = useWikiPages(campaignId);
  const { data: membership } = useMyMembership(campaignId);
  const isDm = membership?.role === "dm";

  return (
    <main className="mx-auto max-w-3xl space-y-6 px-6 py-10">
      <h1 className="text-2xl font-bold">Wiki</h1>

      {isDm ? <WikiPageEditor campaignId={campaignId} /> : null}

      {isLoading ? (
        <p className="text-sm text-muted-foreground">Carregando…</p>
      ) : pages && pages.length > 0 ? (
        <ul className="space-y-2">
          {pages.map((page) => (
            <li key={page.id}>
              <WikiPageCard campaignId={campaignId} page={page} />
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-sm text-muted-foreground">Nenhuma página ainda.</p>
      )}
    </main>
  );
}
