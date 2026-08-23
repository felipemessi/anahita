"""WorldService orchestrates NPC, Location, and Faction management."""

import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.campaigns.domain import CampaignRole
from app.campaigns.models import CampaignMember
from app.catalog.models import Monster
from app.world.models import NPC, Faction, Location
from app.world.schemas import FactionCreate, LocationCreate, NPCCreate


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
        """Create a location; only the campaign's DM may do this."""
        await self._require_dm(campaign_id, requester_id, db)

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
