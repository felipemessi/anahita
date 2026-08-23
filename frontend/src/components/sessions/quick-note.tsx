"use client";

import { useState } from "react";

import { useAddNote } from "@/hooks/use-session";

/**
 * Compact "add note" form: a content field plus, for the DM only, a
 * checkbox to mark the note private (PRD §7.5 — only the DM may do this,
 * enforced again server-side).
 */
export function QuickNote({ sessionId, isDm }: { sessionId: string; isDm: boolean }) {
  const [content, setContent] = useState("");
  const [isPrivate, setIsPrivate] = useState(false);
  const addNote = useAddNote(sessionId);

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!content.trim()) return;
    addNote.mutate(
      { content: content.trim(), is_private: isDm ? isPrivate : false },
      {
        onSuccess: () => {
          setContent("");
          setIsPrivate(false);
        },
      },
    );
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-2">
      <textarea
        value={content}
        onChange={(event) => setContent(event.target.value)}
        placeholder="Adicionar nota…"
        rows={2}
        className="w-full resize-none rounded-md border border-border bg-background px-3 py-2 text-sm"
      />
      <div className="flex items-center justify-between">
        {isDm ? (
          <label className="flex items-center gap-2 text-sm text-muted-foreground">
            <input
              type="checkbox"
              checked={isPrivate}
              onChange={(event) => setIsPrivate(event.target.checked)}
            />
            Nota privada (só o DM vê)
          </label>
        ) : (
          <span />
        )}
        <button
          type="submit"
          disabled={!content.trim() || addNote.isPending}
          className="rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground hover:opacity-90 disabled:opacity-50"
        >
          Adicionar
        </button>
      </div>
      {addNote.isError ? (
        <p role="alert" className="text-sm text-destructive">
          Não foi possível adicionar a nota.
        </p>
      ) : null}
    </form>
  );
}
