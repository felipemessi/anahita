"""Sessions domain enums and invariants."""

from enum import StrEnum


class SessionStatus(StrEnum):
    """Lifecycle status of a game session."""

    planned = "planned"
    in_progress = "in_progress"
    completed = "completed"


class OnlyDmCanWritePrivateNoteError(ValueError):
    """Raised when a non-DM tries to author a private SessionNote."""


def validate_note_author(*, is_private: bool, author_is_dm: bool) -> None:
    """Enforce that only the campaign's DM may author a private SessionNote.

    `SessionNote.is_private=True` means "only the DM sees it" (PRD §7.5) — so
    only the DM may create one; any other member's notes are always public.
    """
    if is_private and not author_is_dm:
        raise OnlyDmCanWritePrivateNoteError(
            "Only the campaign's DM can write a private session note."
        )
