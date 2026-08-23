"""WorldService orchestrates NPC, Location, and Faction management."""

import uuid
from collections import defaultdict

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.campaigns.domain import CampaignRole
from app.campaigns.models import CampaignMember
from app.catalog.models import Monster
from app.queries.world_queries import search_world_entities
from app.sessions.models import Session
from app.world.domain import LocationCycleError, validate_no_parent_cycle
from app.world.models import (
    NPC,
    Faction,
    FactionRelationship,
    Location,
    LocationSession,
    NPCFaction,
    NPCLocation,
    NPCSession,
)
from app.world.schemas import (
    FactionCreate,
    FactionRelationshipCreate,
    LocationCreate,
    LocationParentUpdate,
    LocationSessionCreate,
    LocationTreeNode,
    NPCCreate,
    NPCFactionCreate,
    NPCLocationCreate,
    NPCSessionCreate,
    WorldSearchResult,
)


class WorldService:
    """Orchestrates creation/listing of NPCs, Locations, and Factions."""

    async def create_npc(
        self,
        campaign_id: uuid.UUID,
        requester_id: uuid.UUID,
        data: NPCCreate,
        db: AsyncSession,
    ) -> NPC:
        """Create an NPC; only the campaign's DM may do this.

        `stat_block_id`, when given, must reference an SRD monster or a
        homebrew monster scoped to this same campaign — never another
        campaign's homebrew.
        """
        await self._require_dm(campaign_id, requester_id, db)
        if data.stat_block_id is not None:
            await self._require_visible_monster(campaign_id, data.stat_block_id, db)

        npc = NPC(
            campaign_id=campaign_id,
            name=data.name,
            race=data.race,
            occupation=data.occupation,
            description=data.description,
            personality=data.personality,
            is_alive=data.is_alive,
            stat_block_id=data.stat_block_id,
        )
        db.add(npc)
        await db.commit()
        await db.refresh(npc)
        return npc

    async def list_npcs(
        self, campaign_id: uuid.UUID, requester_id: uuid.UUID, db: AsyncSession
    ) -> list[NPC]:
        """List a campaign's NPCs; requester must be a member."""
        await self._require_membership(campaign_id, requester_id, db)
        result = await db.execute(
            select(NPC).where(NPC.campaign_id == campaign_id).order_by(NPC.created_at)
        )
        return list(result.scalars().all())

    async def create_location(
        self,
        campaign_id: uuid.UUID,
        requester_id: uuid.UUID,
        data: LocationCreate,
        db: AsyncSession,
    ) -> Location:
        """Create a location; only the campaign's DM may do this.

        `parent_location_id`, when given, must belong to this same campaign.
        """
        await self._require_dm(campaign_id, requester_id, db)
        if data.parent_location_id is not None:
            parent = await self._require_location(data.parent_location_id, db)
            if parent.campaign_id != campaign_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Location not found"
                )

        location = Location(
            campaign_id=campaign_id,
            name=data.name,
            location_type=data.location_type,
            description=data.description,
            parent_location_id=data.parent_location_id,
        )
        db.add(location)
        await db.commit()
        await db.refresh(location)
        return location

    async def list_locations(
        self, campaign_id: uuid.UUID, requester_id: uuid.UUID, db: AsyncSession
    ) -> list[Location]:
        """List a campaign's locations; requester must be a member."""
        await self._require_membership(campaign_id, requester_id, db)
        result = await db.execute(
            select(Location)
            .where(Location.campaign_id == campaign_id)
            .order_by(Location.name)
        )
        return list(result.scalars().all())

    async def update_location_parent(
        self,
        location_id: uuid.UUID,
        requester_id: uuid.UUID,
        data: LocationParentUpdate,
        db: AsyncSession,
    ) -> Location:
        """Reparent a location; only the campaign's DM may do this.

        Rejects a new parent from another campaign, and any parent that
        would make `location_id` an ancestor of itself.
        """
        location = await self._require_location(location_id, db)
        await self._require_dm(location.campaign_id, requester_id, db)

        ancestor_ids: set[uuid.UUID] = set()
        if data.parent_location_id is not None:
            new_parent = await self._require_location(data.parent_location_id, db)
            if new_parent.campaign_id != location.campaign_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Location not found"
                )
            ancestor_ids = await self._collect_ancestor_ids(new_parent.id, db)

        try:
            validate_no_parent_cycle(
                location_id=location.id,
                new_parent_id=data.parent_location_id,
                new_parent_ancestor_ids=ancestor_ids,
            )
        except LocationCycleError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
            ) from exc

        location.parent_location_id = data.parent_location_id
        await db.commit()
        await db.refresh(location)
        return location

    async def get_location_tree(
        self, campaign_id: uuid.UUID, requester_id: uuid.UUID, db: AsyncSession
    ) -> list[LocationTreeNode]:
        """Return a campaign's locations nested by `parent_location_id`."""
        locations = await self.list_locations(campaign_id, requester_id, db)
        by_parent: dict[uuid.UUID | None, list[Location]] = defaultdict(list)
        for location in locations:
            by_parent[location.parent_location_id].append(location)

        def build(parent_id: uuid.UUID | None) -> list[LocationTreeNode]:
            return [
                LocationTreeNode(
                    id=loc.id,
                    name=loc.name,
                    location_type=loc.location_type,
                    children=build(loc.id),
                )
                for loc in by_parent.get(parent_id, [])
            ]

        return build(None)

    async def create_faction(
        self,
        campaign_id: uuid.UUID,
        requester_id: uuid.UUID,
        data: FactionCreate,
        db: AsyncSession,
    ) -> Faction:
        """Create a faction; only the campaign's DM may do this."""
        await self._require_dm(campaign_id, requester_id, db)

        faction = Faction(
            campaign_id=campaign_id,
            name=data.name,
            description=data.description,
            alignment=data.alignment,
            influence_level=data.influence_level,
        )
        db.add(faction)
        await db.commit()
        await db.refresh(faction)
        return faction

    async def list_factions(
        self, campaign_id: uuid.UUID, requester_id: uuid.UUID, db: AsyncSession
    ) -> list[Faction]:
        """List a campaign's factions; requester must be a member."""
        await self._require_membership(campaign_id, requester_id, db)
        result = await db.execute(
            select(Faction)
            .where(Faction.campaign_id == campaign_id)
            .order_by(Faction.name)
        )
        return list(result.scalars().all())

    async def search(
        self,
        campaign_id: uuid.UUID,
        requester_id: uuid.UUID,
        query_text: str,
        db: AsyncSession,
    ) -> list[WorldSearchResult]:
        """Search a campaign's NPCs, Locations, and Factions by name/description.

        Postgres-only (uses `tsvector`); requester must be a campaign member.
        """
        await self._require_membership(campaign_id, requester_id, db)
        hits = await search_world_entities(campaign_id, query_text, db)
        return [
            WorldSearchResult(
                entity_type=hit.entity_type,
                id=hit.id,
                name=hit.name,
                snippet=hit.snippet,
            )
            for hit in hits
        ]

    async def link_npc_faction(
        self,
        npc_id: uuid.UUID,
        requester_id: uuid.UUID,
        data: NPCFactionCreate,
        db: AsyncSession,
    ) -> NPCFaction:
        """Link an NPC to a Faction from their own campaign; DM-only."""
        npc = await self._require_npc(npc_id, db)
        await self._require_dm(npc.campaign_id, requester_id, db)
        faction = await self._require_same_campaign_faction(
            data.faction_id, npc.campaign_id, db
        )

        link = NPCFaction(
            npc_id=npc.id,
            faction_id=faction.id,
            role_in_faction=data.role_in_faction,
        )
        db.add(link)
        await db.commit()
        await db.refresh(link)
        return link

    async def list_npc_factions(
        self, npc_id: uuid.UUID, requester_id: uuid.UUID, db: AsyncSession
    ) -> list[NPCFaction]:
        """List an NPC's faction links; requester must be a campaign member."""
        npc = await self._require_npc(npc_id, db)
        await self._require_membership(npc.campaign_id, requester_id, db)
        result = await db.execute(select(NPCFaction).where(NPCFaction.npc_id == npc.id))
        return list(result.scalars().all())

    async def link_npc_location(
        self,
        npc_id: uuid.UUID,
        requester_id: uuid.UUID,
        data: NPCLocationCreate,
        db: AsyncSession,
    ) -> NPCLocation:
        """Link an NPC to a Location from their own campaign; DM-only."""
        npc = await self._require_npc(npc_id, db)
        await self._require_dm(npc.campaign_id, requester_id, db)
        location = await self._require_location(data.location_id, db)
        if location.campaign_id != npc.campaign_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Location not found"
            )

        link = NPCLocation(
            npc_id=npc.id,
            location_id=location.id,
            presence_type=data.presence_type,
        )
        db.add(link)
        await db.commit()
        await db.refresh(link)
        return link

    async def list_npc_locations(
        self, npc_id: uuid.UUID, requester_id: uuid.UUID, db: AsyncSession
    ) -> list[NPCLocation]:
        """List an NPC's location links; requester must be a campaign member."""
        npc = await self._require_npc(npc_id, db)
        await self._require_membership(npc.campaign_id, requester_id, db)
        result = await db.execute(
            select(NPCLocation).where(NPCLocation.npc_id == npc.id)
        )
        return list(result.scalars().all())

    async def link_npc_session(
        self,
        npc_id: uuid.UUID,
        requester_id: uuid.UUID,
        data: NPCSessionCreate,
        db: AsyncSession,
    ) -> NPCSession:
        """Link an NPC to a Session appearance from their own campaign; DM-only."""
        npc = await self._require_npc(npc_id, db)
        await self._require_dm(npc.campaign_id, requester_id, db)
        session = await self._require_same_campaign_session(
            data.session_id, npc.campaign_id, db
        )

        link = NPCSession(
            npc_id=npc.id,
            session_id=session.id,
            appearance_note=data.appearance_note,
        )
        db.add(link)
        await db.commit()
        await db.refresh(link)
        return link

    async def list_npc_sessions(
        self, npc_id: uuid.UUID, requester_id: uuid.UUID, db: AsyncSession
    ) -> list[NPCSession]:
        """List an NPC's session appearances; requester must be a campaign member."""
        npc = await self._require_npc(npc_id, db)
        await self._require_membership(npc.campaign_id, requester_id, db)
        result = await db.execute(select(NPCSession).where(NPCSession.npc_id == npc.id))
        return list(result.scalars().all())

    async def link_location_session(
        self,
        location_id: uuid.UUID,
        requester_id: uuid.UUID,
        data: LocationSessionCreate,
        db: AsyncSession,
    ) -> LocationSession:
        """Link a Location to a Session visit from their own campaign; DM-only."""
        location = await self._require_location(location_id, db)
        await self._require_dm(location.campaign_id, requester_id, db)
        session = await self._require_same_campaign_session(
            data.session_id, location.campaign_id, db
        )

        link = LocationSession(
            location_id=location.id,
            session_id=session.id,
            visit_note=data.visit_note,
        )
        db.add(link)
        await db.commit()
        await db.refresh(link)
        return link

    async def list_location_sessions(
        self, location_id: uuid.UUID, requester_id: uuid.UUID, db: AsyncSession
    ) -> list[LocationSession]:
        """List a Location's session visits; requester must be a campaign member."""
        location = await self._require_location(location_id, db)
        await self._require_membership(location.campaign_id, requester_id, db)
        result = await db.execute(
            select(LocationSession).where(LocationSession.location_id == location.id)
        )
        return list(result.scalars().all())

    async def link_faction_relationship(
        self,
        faction_a_id: uuid.UUID,
        requester_id: uuid.UUID,
        data: FactionRelationshipCreate,
        db: AsyncSession,
    ) -> FactionRelationship:
        """Set a relationship between two Factions from the same campaign; DM-only."""
        faction_a = await self._require_faction(faction_a_id, db)
        await self._require_dm(faction_a.campaign_id, requester_id, db)
        if data.faction_b_id == faction_a_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A faction cannot have a relationship with itself",
            )
        faction_b = await self._require_same_campaign_faction(
            data.faction_b_id, faction_a.campaign_id, db
        )

        link = FactionRelationship(
            faction_a_id=faction_a.id,
            faction_b_id=faction_b.id,
            relationship_type=data.relationship_type,
        )
        db.add(link)
        await db.commit()
        await db.refresh(link)
        return link

    async def list_faction_relationships(
        self, faction_id: uuid.UUID, requester_id: uuid.UUID, db: AsyncSession
    ) -> list[FactionRelationship]:
        """List a Faction's relationships (as either side); membership required."""
        faction = await self._require_faction(faction_id, db)
        await self._require_membership(faction.campaign_id, requester_id, db)
        result = await db.execute(
            select(FactionRelationship).where(
                (FactionRelationship.faction_a_id == faction.id)
                | (FactionRelationship.faction_b_id == faction.id)
            )
        )
        return list(result.scalars().all())

    async def _require_npc(self, npc_id: uuid.UUID, db: AsyncSession) -> NPC:
        """Fetch an NPC by id, or raise 404."""
        result = await db.execute(select(NPC).where(NPC.id == npc_id))
        npc = result.scalar_one_or_none()
        if npc is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="NPC not found"
            )
        return npc

    async def _require_faction(
        self, faction_id: uuid.UUID, db: AsyncSession
    ) -> Faction:
        """Fetch a faction by id, or raise 404."""
        result = await db.execute(select(Faction).where(Faction.id == faction_id))
        faction = result.scalar_one_or_none()
        if faction is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Faction not found"
            )
        return faction

    async def _require_same_campaign_faction(
        self, faction_id: uuid.UUID, campaign_id: uuid.UUID, db: AsyncSession
    ) -> Faction:
        """Fetch a faction, requiring it belongs to `campaign_id`, or raise 404."""
        faction = await self._require_faction(faction_id, db)
        if faction.campaign_id != campaign_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Faction not found"
            )
        return faction

    async def _require_same_campaign_session(
        self, session_id: uuid.UUID, campaign_id: uuid.UUID, db: AsyncSession
    ) -> Session:
        """Fetch a session, requiring it belongs to `campaign_id`, or raise 404."""
        result = await db.execute(select(Session).where(Session.id == session_id))
        session = result.scalar_one_or_none()
        if session is None or session.campaign_id != campaign_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
            )
        return session

    async def _require_location(
        self, location_id: uuid.UUID, db: AsyncSession
    ) -> Location:
        """Fetch a location by id, or raise 404."""
        result = await db.execute(select(Location).where(Location.id == location_id))
        location = result.scalar_one_or_none()
        if location is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Location not found"
            )
        return location

    async def _collect_ancestor_ids(
        self, start_id: uuid.UUID, db: AsyncSession
    ) -> set[uuid.UUID]:
        """Walk `parent_location_id` upward from `start_id`, inclusive of it."""
        ancestor_ids: set[uuid.UUID] = set()
        current_id: uuid.UUID | None = start_id
        while current_id is not None:
            ancestor_ids.add(current_id)
            result = await db.execute(
                select(Location.parent_location_id).where(Location.id == current_id)
            )
            current_id = result.scalar_one_or_none()
        return ancestor_ids

    async def _require_visible_monster(
        self, campaign_id: uuid.UUID, monster_id: uuid.UUID, db: AsyncSession
    ) -> Monster:
        """Fetch a monster usable as a stat block from this campaign, or raise.

        Visible means: an SRD monster (`campaign_id IS NULL`) or a homebrew
        monster belonging to this exact campaign — never another campaign's.
        """
        result = await db.execute(select(Monster).where(Monster.id == monster_id))
        monster = result.scalar_one_or_none()
        if monster is None or (
            monster.is_custom and monster.campaign_id != campaign_id
        ):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Monster not found"
            )
        return monster

    async def _require_membership(
        self, campaign_id: uuid.UUID, requester_id: uuid.UUID, db: AsyncSession
    ) -> CampaignMember:
        """Fetch the requester's membership in `campaign_id`, or raise 403."""
        result = await db.execute(
            select(CampaignMember).where(
                CampaignMember.campaign_id == campaign_id,
                CampaignMember.user_id == requester_id,
            )
        )
        member = result.scalar_one_or_none()
        if member is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not a member of this campaign",
            )
        return member

    async def _require_dm(
        self, campaign_id: uuid.UUID, requester_id: uuid.UUID, db: AsyncSession
    ) -> CampaignMember:
        """Fetch the requester's membership, requiring the DM role, or raise 403."""
        member = await self._require_membership(campaign_id, requester_id, db)
        if member.role != CampaignRole.dm:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the campaign's DM can do this",
            )
        return member
