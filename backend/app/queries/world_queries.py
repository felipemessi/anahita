"""Cross-entity full-text search over NPCs, Locations, Factions, and Wiki Pages.

Postgres-only: uses `tsvector`/`plainto_tsquery`, so this only works against
Postgres — the world domain's SQLite test suite never exercises this module.
"""

import uuid
from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

_SEARCH_SQL = text(
    """
    SELECT 'npc' AS entity_type, id, name, description AS snippet,
           ts_rank(
               to_tsvector('english', name || ' ' || description),
               plainto_tsquery('english', :query)
           ) AS rank
    FROM npcs
    WHERE campaign_id = :campaign_id
      AND to_tsvector('english', name || ' ' || description)
          @@ plainto_tsquery('english', :query)

    UNION ALL

    SELECT 'location' AS entity_type, id, name, description AS snippet,
           ts_rank(
               to_tsvector('english', name || ' ' || description),
               plainto_tsquery('english', :query)
           ) AS rank
    FROM locations
    WHERE campaign_id = :campaign_id
      AND to_tsvector('english', name || ' ' || description)
          @@ plainto_tsquery('english', :query)

    UNION ALL

    SELECT 'faction' AS entity_type, id, name, description AS snippet,
           ts_rank(
               to_tsvector('english', name || ' ' || description),
               plainto_tsquery('english', :query)
           ) AS rank
    FROM factions
    WHERE campaign_id = :campaign_id
      AND to_tsvector('english', name || ' ' || description)
          @@ plainto_tsquery('english', :query)

    UNION ALL

    SELECT 'wiki_page' AS entity_type, id, title AS name, content AS snippet,
           ts_rank(
               to_tsvector('english', title || ' ' || content),
               plainto_tsquery('english', :query)
           ) AS rank
    FROM wiki_pages
    WHERE campaign_id = :campaign_id
      AND to_tsvector('english', title || ' ' || content)
          @@ plainto_tsquery('english', :query)

    ORDER BY rank DESC
    LIMIT 50
    """
)


@dataclass
class WorldSearchHit:
    """One cross-entity search result."""

    entity_type: str
    id: uuid.UUID
    name: str
    snippet: str


async def search_world_entities(
    campaign_id: uuid.UUID, query_text: str, db: AsyncSession
) -> list[WorldSearchHit]:
    """Search a campaign's NPCs, Locations, and Factions by name/description.

    Ranked by Postgres's `ts_rank`, best match first. `query_text` is passed
    through `plainto_tsquery`, so it accepts plain natural-language text
    rather than raw tsquery syntax.
    """
    result = await db.execute(
        _SEARCH_SQL, {"campaign_id": campaign_id, "query": query_text}
    )
    return [
        WorldSearchHit(
            entity_type=row.entity_type, id=row.id, name=row.name, snippet=row.snippet
        )
        for row in result.all()
    ]
