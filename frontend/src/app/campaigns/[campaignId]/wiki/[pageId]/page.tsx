"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import ReactMarkdown from "react-markdown";

import { WikiPageLinks } from "@/components/wiki/wiki-page-links";
import { useMyMembership } from "@/hooks/use-campaign";
import { useDeleteWikiPage, useUpdateWikiPage, useWikiPage } from "@/hooks/use-wiki";

export default function WikiPageDetailPage() {
  const { campaignId, pageId } = useParams<{ campaignId: string; pageId: string }>();
  const router = useRouter();
  const { data: page, isLoading } = useWikiPage(pageId);
  const { data: membership } = useMyMembership(campaignId);
  const isDm = membership?.role === "dm";

  const [isEditing, setIsEditing] = useState(false);
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [tags, setTags] = useState("");
  const updatePage = useUpdateWikiPage(campaignId, pageId);
  const deletePage = useDeleteWikiPage(campaignId);

  function startEditing() {
    if (!page) return;
    setTitle(page.title);
    setContent(page.content);
    setTags(page.tags ?? "");
    setIsEditing(true);
  }

  function handleSave(event: React.FormEvent) {
    event.preventDefault();
    if (!title.trim()) return;
    updatePage.mutate(
      { title: title.trim(), content, tags: tags.trim() || null },
      { onSuccess: () => setIsEditing(false) },
    );
  }

  function handleDelete() {
    deletePage.mutate(pageId, {
      onSuccess: () => router.push(`/campaigns/${campaignId}/wiki`),
    });
  }

  if (isLoading) {
    return (
      <main className="mx-auto max-w-3xl px-6 py-10">
        <p className="text-sm text-muted-foreground">Carregando…</p>
      </main>
    );
  }
  if (!page) {
    return (
      <main className="mx-auto max-w-3xl px-6 py-10">
        <p className="text-sm text-muted-foreground">Página não encontrada.</p>
      </main>
    );
  }

  const tagList = page.tags
    ?.split(",")
    .map((tag) => tag.trim())
    .filter(Boolean);

  return (
    <main className="mx-auto max-w-3xl space-y-6 px-6 py-10">
      {isEditing ? (
        <form onSubmit={handleSave} className="space-y-2">
          <input
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
          />
          <textarea
            value={content}
            onChange={(event) => setContent(event.target.value)}
            rows={10}
            className="w-full resize-y rounded-md border border-border bg-background px-3 py-2 font-mono text-sm"
          />
          <input
            value={tags}
            onChange={(event) => setTags(event.target.value)}
            placeholder="Tags separadas por vírgula (opcional)"
            className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
          />
          <div className="flex gap-2">
            <button
              type="submit"
              disabled={!title.trim() || updatePage.isPending}
              className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:opacity-90 disabled:opacity-50"
            >
              Salvar
            </button>
            <button
              type="button"
              onClick={() => setIsEditing(false)}
              className="rounded-md border border-border px-4 py-2 text-sm hover:bg-secondary/50"
            >
              Cancelar
            </button>
          </div>
        </form>
      ) : (
        <>
          <header className="flex items-center justify-between gap-2">
            <div>
              <h1 className="text-2xl font-bold">{page.title}</h1>
              {tagList && tagList.length > 0 ? (
                <div className="mt-1 flex gap-1">
                  {tagList.map((tag) => (
                    <span
                      key={tag}
                      className="rounded-full border border-border px-2 py-0.5 text-xs text-muted-foreground"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              ) : null}
            </div>
            {isDm ? (
              <div className="flex shrink-0 gap-2 text-xs">
                <button
                  type="button"
                  onClick={startEditing}
                  className="text-muted-foreground underline hover:no-underline"
                >
                  Editar
                </button>
                <button
                  type="button"
                  onClick={handleDelete}
                  className="text-destructive underline hover:no-underline"
                >
                  Apagar
                </button>
              </div>
            ) : null}
          </header>

          <article className="space-y-3 text-sm leading-relaxed [&_a]:underline [&_h1]:text-lg [&_h1]:font-bold [&_h2]:text-base [&_h2]:font-semibold [&_li]:ml-4 [&_li]:list-disc [&_strong]:font-semibold">
            <ReactMarkdown>{page.content}</ReactMarkdown>
          </article>
        </>
      )}

      <WikiPageLinks
        campaignId={campaignId}
        pageId={page.id}
        links={page.links}
        isDm={isDm}
      />
    </main>
  );
}
