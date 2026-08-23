"use client";

import { useSessionNotes } from "@/hooks/use-session";
import { useUserProfiles } from "@/hooks/use-users";

import { QuickNote } from "./quick-note";

/**
 * Full notes panel for a session: the list of notes visible to the current
 * viewer (the backend already filters private notes out for non-DM
 * viewers — see SessionService.list_notes) plus the add-note form.
 */
export function NoteEditor({ sessionId, isDm }: { sessionId: string; isDm: boolean }) {
  const { data: notes, isLoading } = useSessionNotes(sessionId);
  const authorIds = [...new Set((notes ?? []).map((note) => note.author_id))];
  const { data: authors } = useUserProfiles(authorIds);

  function authorName(authorId: string): string {
    return authors?.find((author) => author.id === authorId)?.username ?? authorId;
  }

  return (
    <section className="space-y-4">
      <h2 className="font-semibold">Notas</h2>

      {isLoading ? (
        <p className="text-sm text-muted-foreground">Carregando…</p>
      ) : notes && notes.length > 0 ? (
        <ul className="space-y-2">
          {notes.map((note) => (
            <li
              key={note.id}
              className="rounded-lg border border-border bg-card px-4 py-3"
            >
              <div className="flex items-center justify-between text-xs text-muted-foreground">
                <span>{authorName(note.author_id)}</span>
                {note.is_private ? (
                  <span className="rounded-full border border-border px-2 py-0.5">
                    Privada
                  </span>
                ) : null}
              </div>
              <p className="mt-1 whitespace-pre-wrap text-sm">{note.content}</p>
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-sm text-muted-foreground">Nenhuma nota ainda.</p>
      )}

      <QuickNote sessionId={sessionId} isDm={isDm} />
    </section>
  );
}
