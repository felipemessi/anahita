import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

const useSessionNotes = vi.fn();
const useAddNote = vi.fn();
const useUserProfiles = vi.fn();

vi.mock("@/hooks/use-session", () => ({
  useSessionNotes: (...args: unknown[]) => useSessionNotes(...args),
  useAddNote: (...args: unknown[]) => useAddNote(...args),
}));
vi.mock("@/hooks/use-users", () => ({
  useUserProfiles: (...args: unknown[]) => useUserProfiles(...args),
}));

import { NoteEditor } from "./note-editor";

describe("NoteEditor", () => {
  it("player never sees another author's private note — the backend already filtered it out", () => {
    // The DM wrote a private note; the backend's list_notes() omits it for
    // non-DM viewers, so the player's `notes` payload simply never contains
    // it — NoteEditor has no client-side filtering logic to get wrong.
    useSessionNotes.mockReturnValue({
      data: [
        {
          id: "note-1",
          session_id: "sess-1",
          author_id: "player-1",
          content: "Público: encontramos um baú",
          is_private: false,
          created_at: "2026-01-01T00:00:00Z",
        },
      ],
      isLoading: false,
    });
    useAddNote.mockReturnValue({ mutate: vi.fn(), isPending: false, isError: false });
    useUserProfiles.mockReturnValue({
      data: [{ id: "player-1", username: "Aria" }],
    });

    render(<NoteEditor sessionId="sess-1" isDm={false} />);

    expect(screen.getByText(/encontramos um baú/i)).toBeInTheDocument();
    expect(screen.queryByText(/privada/i)).not.toBeInTheDocument();
    // Player never sees the "mark private" checkbox either.
    expect(screen.queryByLabelText(/nota privada/i)).not.toBeInTheDocument();
  });

  it("DM sees the private badge on private notes", () => {
    useSessionNotes.mockReturnValue({
      data: [
        {
          id: "note-2",
          session_id: "sess-1",
          author_id: "dm-1",
          content: "Segredo: o vilão é o barão",
          is_private: true,
          created_at: "2026-01-01T00:00:00Z",
        },
      ],
      isLoading: false,
    });
    useAddNote.mockReturnValue({ mutate: vi.fn(), isPending: false, isError: false });
    useUserProfiles.mockReturnValue({ data: [{ id: "dm-1", username: "Mestre" }] });

    render(<NoteEditor sessionId="sess-1" isDm={true} />);

    expect(screen.getByText(/o vilão é o barão/i)).toBeInTheDocument();
    expect(screen.getAllByText(/privada/i).length).toBeGreaterThan(0);
    expect(screen.getByLabelText(/nota privada/i)).toBeInTheDocument();
  });
});
