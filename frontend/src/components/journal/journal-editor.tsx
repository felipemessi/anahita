"use client";

import { useState } from "react";

import { useCreateJournalEntry } from "@/hooks/use-journal";

/** Form to add a new journal entry: title + content. Always DM-only (the route is DM-only). */
export function JournalEditor({ campaignId }: { campaignId: string }) {
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const createEntry = useCreateJournalEntry(campaignId);

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!title.trim()) return;
    createEntry.mutate(
      { title: title.trim(), content: content.trim() },
      {
        onSuccess: () => {
          setTitle("");
          setContent("");
        },
      },
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-2">
      <input
        value={title}
        onChange={(event) => setTitle(event.target.value)}
        placeholder="Título da entrada"
        className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
      />
      <textarea
        value={content}
        onChange={(event) => setContent(event.target.value)}
        placeholder="O que aconteceu?"
        rows={4}
        className="w-full resize-none rounded-md border border-border bg-background px-3 py-2 text-sm"
      />
      <button
        type="submit"
        disabled={!title.trim() || createEntry.isPending}
        className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:opacity-90 disabled:opacity-50"
      >
        Adicionar entrada
      </button>
      {createEntry.isError ? (
        <p role="alert" className="text-sm text-destructive">
          Não foi possível criar a entrada.
        </p>
      ) : null}
    </form>
  );
}
