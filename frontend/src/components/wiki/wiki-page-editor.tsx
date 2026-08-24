"use client";

import { useState } from "react";

import { useCreateWikiPage } from "@/hooks/use-wiki";

/** Form to create a new wiki page: title, markdown content, and free-text tags. DM-only. */
export function WikiPageEditor({ campaignId }: { campaignId: string }) {
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [tags, setTags] = useState("");
  const createPage = useCreateWikiPage(campaignId);

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!title.trim()) return;
    createPage.mutate(
      { title: title.trim(), content, tags: tags.trim() || null },
      {
        onSuccess: () => {
          setTitle("");
          setContent("");
          setTags("");
        },
      },
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-2 rounded-lg border border-border bg-card p-4">
      <p className="text-sm font-medium">Nova página</p>
      <input
        value={title}
        onChange={(event) => setTitle(event.target.value)}
        placeholder="Título"
        className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
      />
      <textarea
        value={content}
        onChange={(event) => setContent(event.target.value)}
        placeholder="Conteúdo em markdown"
        rows={6}
        className="w-full resize-y rounded-md border border-border bg-background px-3 py-2 font-mono text-sm"
      />
      <input
        value={tags}
        onChange={(event) => setTags(event.target.value)}
        placeholder="Tags separadas por vírgula (opcional)"
        className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
      />
      <button
        type="submit"
        disabled={!title.trim() || createPage.isPending}
        className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:opacity-90 disabled:opacity-50"
      >
        Criar página
      </button>
      {createPage.isError ? (
        <p role="alert" className="text-sm text-destructive">
          Não foi possível criar a página.
        </p>
      ) : null}
    </form>
  );
}
