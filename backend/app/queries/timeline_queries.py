"""Cross-domain query merging Session-derived and manual timeline entries.

Fuses two sources into one chronological list (PRD §7.10):
- **Automatic entries**: one virtual (never persisted) entry per `Session`
  that has a `summary`, ordered by `session_number * 1000` — leaving gaps
  for manual events to be interleaved between sessions.
- **Manual entries**: persisted `TimelineEvent` rows, ordered by their own
  explicit `sort_order`.
"""

import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.sessions.models import Session
from app.timeline.models import TimelineEvent

_SESSION_SORT_ORDER_STEP = 1000


@dataclass
class TimelineEntry:
    """One entry on a campaign's fused timeline — automatic or manual."""

    entry_type: str
    id: uuid.UUID
    title: str
    description: str | None
    session_id: uuid.UUID | None
    in_game_date: str | None
    sort_order: int
    created_at: datetime


async def get_campaign_timeline(
    campaign_id: uuid.UUID, db: AsyncSession
) -> list[TimelineEntry]:
    """Return a campaign's timeline, automatic and manual entries merged.

    Automatic entries are computed here from `Session` rows with a
    non-empty `summary` — never persisted — and interleaved with manual
    `TimelineEvent` rows by `sort_order`.
    """
    sessions_result = await db.execute(
        select(Session).where(
            Session.campaign_id == campaign_id, Session.summary.is_not(None)
        )
    )
    automatic_entries = [
        TimelineEntry(
            entry_type="session",
            id=s.id,
            title=s.title,
            description=s.summary,
            session_id=s.id,
            in_game_date=None,
            sort_order=s.session_number * _SESSION_SORT_ORDER_STEP,
            created_at=s.created_at,
        )
        for s in sessions_result.scalars().all()
        if s.summary
    ]

    events_result = await db.execute(
        select(TimelineEvent).where(TimelineEvent.campaign_id == campaign_id)
    )
    manual_entries = [
        TimelineEntry(
            entry_type="event",
            id=e.id,
            title=e.title,
            description=e.description,
            session_id=e.session_id,
            in_game_date=e.in_game_date,
            sort_order=e.sort_order,
            created_at=e.created_at,
        )
        for e in events_result.scalars().all()
    ]

    all_entries = automatic_entries + manual_entries
    return sorted(all_entries, key=lambda entry: entry.sort_order)
