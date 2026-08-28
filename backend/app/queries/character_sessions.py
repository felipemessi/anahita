"""Cross-domain read: which sessions a character has actually appeared in.

`Character` has no direct relation to `Session` (see backlog Fase 10,
história 4 for the design note). Membership is derived from real combat
participation — `EncounterParticipant.character_id` -> `Encounter.session_id`
-> `Session` — rather than an explicit list the DM would have to keep in
sync by hand. A character who has never been added to an encounter (e.g.
before their first session, or a purely narrative character) simply has no
sessions yet.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.combat.models import Encounter, EncounterParticipant
from app.sessions.models import Session


async def get_sessions_for_character(
    character_id: uuid.UUID, db: AsyncSession
) -> list[Session]:
    """Return the sessions a character has participated in combat during.

    Ordered by `session_number` (the campaign's standard session order).
    A session is included once even if the character appeared in more than
    one encounter within it (`distinct()` on the joined session id).
    """
    result = await db.execute(
        select(Session)
        .join(Encounter, Encounter.session_id == Session.id)
        .join(
            EncounterParticipant,
            EncounterParticipant.encounter_id == Encounter.id,
        )
        .where(EncounterParticipant.character_id == character_id)
        .distinct()
        .order_by(Session.session_number)
    )
    return list(result.scalars().all())
