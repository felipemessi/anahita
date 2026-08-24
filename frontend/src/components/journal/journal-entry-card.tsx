"use client";

import { useState } from "react";

import { useDeleteJournalEntry, useUpdateJournalEntry } from "@/hooks/use-journal";
import type { JournalEntry } from "@/types/journal";

/** A journal entry with inline edit/delete. Always DM-only (the route is DM-only). */
export function JournalEntryCard({
  campaignId,
  entry,
}: {
  campaignId: string;
  entry: JournalEntry;
}) {
  const [isEditing, setIsEditing] = useState(false);
  const [title, setTitle] = useState(entry.title);
  const [content, setContent] = useState(entry.content);
  const updateEntry = useUpdateJournalEntry(campaignId);
  const deleteEntry = useDeleteJournalEntry(campaignId);

  function handleSave(event: React.FormEvent) {
    event.preventDefault();
    if (!title.trim()) return;
    updateEntry.mutate(
      { entryId: entry.id, data: { title: title.trim(), content } },
      { onSuccess: () => setIsEditing(false) },
    );
  }

  if (isEditing) {
    return (
      <form
        onSubmit={handleSave}
        className="space-y-2 rounded-lg border border-border bg-card p-4"
      >
        <input
          value={title}
          onChange={(event) => setTitle(event.target.value)}
          className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
        />
        <textarea
          value={content}
          onChange={(event) => setContent(event.target.value)}
          rows={4}
          className="w-full resize-none rounded-md border border-border bg-background px-3 py-2 text-sm"
        />
        <div className="flex gap-2">
          <button
            type="submit"
            disabled={!title.trim() || updateEntry.isPending}
            className="rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground hover:opacity-90 disabled:opacity-50"
          >
            Salvar
          </button>
          <button
            type="button"
            onClick={() => setIsEditing(false)}
            className="rounded-md border border-border px-3 py-1.5 text-sm hover:bg-secondary/50"
          >
            Cancelar
          </button>
        </div>
      </form>
    );
  }

  return (
    <article className="space-y-2 rounded-lg border border-border bg-card p-4">
      <header className="flex items-center justify-between gap-2">
        <p className="font-medium">{entry.title}</p>
        <div className="flex shrink-0 gap-2 text-xs">
          <button
            type="button"
            onClick={() => setIsEditing(true)}
            className="text-muted-foreground underline hover:no-underline"
          >
            Editar
          </button>
          <button
            type="button"
            onClick={() => deleteEntry.mutate(entry.id)}
            className="text-destructive underline hover:no-underline"
          >
            Apagar
          </button>
        </div>
      </header>
      {entry.content ? (
        <p className="whitespace-pre-wrap text-sm">{entry.content}</p>
      ) : null}
      <p className="text-xs text-muted-foreground">
        {new Date(entry.created_at).toLocaleDateString("pt-BR")}
      </p>
    </article>
  );
}
