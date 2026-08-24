"""WikiService orchestrates wiki page and page-link management."""

import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.campaigns.domain import CampaignRole
from app.campaigns.models import CampaignMember
from app.wiki.domain import (
    WikiPageLinkKindError,
    slugify,
    validate_wiki_link_kind,
)
from app.wiki.models import WikiPage, WikiPageLink
from app.wiki.schemas import WikiPageCreate, WikiPageLinkCreate, WikiPageUpdate
from app.world.models import NPC, Faction, Location


class WikiService:
    """Orchestrates WikiPage CRUD and WikiPageLink creation/removal."""

    async def create_page(
        self,
        campaign_id: uuid.UUID,
        requester_id: uuid.UUID,
        data: WikiPageCreate,
        db: AsyncSession,
    ) -> WikiPage:
        """Create a wiki page; only the campaign's DM may do this."""
        await self._require_dm(campaign_id, requester_id, db)
        slug = await self._unique_slug(campaign_id, data.title, db)

        page = WikiPage(
            campaign_id=campaign_id,
            title=data.title,
            slug=slug,
            content=data.content,
            tags=data.tags,
            created_by_id=requester_id,
        )
        db.add(page)
        await db.commit()
        await db.refresh(page)
        return page

    async def list_pages(
        self, campaign_id: uuid.UUID, requester_id: uuid.UUID, db: AsyncSession
    ) -> list[WikiPage]:
        """List a campaign's wiki pages; requester must be a member."""
        await self._require_membership(campaign_id, requester_id, db)
        result = await db.execute(
            select(WikiPage)
            .where(WikiPage.campaign_id == campaign_id)
            .order_by(WikiPage.title)
        )
        return list(result.scalars().all())

    async def get_page(
        self, page_id: uuid.UUID, requester_id: uuid.UUID, db: AsyncSession
    ) -> tuple[WikiPage, list[WikiPageLink]]:
        """Fetch a wiki page and its links; requester must be a member."""
        page = await self._require_page(page_id, db)
        await self._require_membership(page.campaign_id, requester_id, db)
        result = await db.execute(
            select(WikiPageLink).where(WikiPageLink.wiki_page_id == page.id)
        )
        return page, list(result.scalars().all())

    async def update_page(
        self,
        page_id: uuid.UUID,
        requester_id: uuid.UUID,
        data: WikiPageUpdate,
        db: AsyncSession,
    ) -> WikiPage:
        """Update a wiki page's title/content/tags. DM-only.

        Changing `title` regenerates `slug`, excluding the page's own
        current slug from the uniqueness check.
        """
        page = await self._require_page(page_id, db)
        await self._require_dm(page.campaign_id, requester_id, db)

        if data.title is not None:
            page.title = data.title
            page.slug = await self._unique_slug(
                page.campaign_id, data.title, db, exclude_page_id=page.id
            )
        if data.content is not None:
            page.content = data.content
        if data.tags is not None:
            page.tags = data.tags
        await db.commit()
        await db.refresh(page)
        return page

    async def delete_page(
        self, page_id: uuid.UUID, requester_id: uuid.UUID, db: AsyncSession
    ) -> None:
        """Delete a wiki page and its links. DM-only."""
        page = await self._require_page(page_id, db)
        await self._require_dm(page.campaign_id, requester_id, db)
        await db.delete(page)
        await db.commit()

    async def create_link(
        self,
        page_id: uuid.UUID,
        requester_id: uuid.UUID,
        data: WikiPageLinkCreate,
        db: AsyncSession,
    ) -> WikiPageLink:
        """Link a wiki page to an NPC, location, or faction. DM-only."""
        page = await self._require_page(page_id, db)
        await self._require_dm(page.campaign_id, requester_id, db)

        try:
            validate_wiki_link_kind(
                npc_id=data.npc_id,
                location_id=data.location_id,
                faction_id=data.faction_id,
            )
        except WikiPageLinkKindError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
            ) from exc

        if data.npc_id is not None:
            await self._require_same_campaign(NPC, data.npc_id, page.campaign_id, db)
        if data.location_id is not None:
            await self._require_same_campaign(
                Location, data.location_id, page.campaign_id, db
            )
        if data.faction_id is not None:
            await self._require_same_campaign(
                Faction, data.faction_id, page.campaign_id, db
            )

        link = WikiPageLink(
            wiki_page_id=page.id,
            npc_id=data.npc_id,
            location_id=data.location_id,
            faction_id=data.faction_id,
        )
        db.add(link)
        await db.commit()
        await db.refresh(link)
        return link

    async def delete_link(
        self,
        page_id: uuid.UUID,
        link_id: uuid.UUID,
        requester_id: uuid.UUID,
        db: AsyncSession,
    ) -> None:
        """Remove a wiki page link. DM-only."""
        page = await self._require_page(page_id, db)
        await self._require_dm(page.campaign_id, requester_id, db)
        result = await db.execute(
            select(WikiPageLink).where(
                WikiPageLink.id == link_id, WikiPageLink.wiki_page_id == page.id
            )
        )
        link = result.scalar_one_or_none()
        if link is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Wiki page link not found"
            )
        await db.delete(link)
        await db.commit()

    async def _unique_slug(
        self,
        campaign_id: uuid.UUID,
        title: str,
        db: AsyncSession,
        *,
        exclude_page_id: uuid.UUID | None = None,
    ) -> str:
        """Derive a slug from `title`, appending a numeric suffix on collision."""
        base_slug = slugify(title)
        slug = base_slug
        suffix = 2
        while await self._slug_taken(campaign_id, slug, db, exclude_page_id):
            slug = f"{base_slug}-{suffix}"
            suffix += 1
        return slug

    async def _slug_taken(
        self,
        campaign_id: uuid.UUID,
        slug: str,
        db: AsyncSession,
        exclude_page_id: uuid.UUID | None,
    ) -> bool:
        """Return whether `slug` is already used by another page in this campaign."""
        stmt = select(WikiPage.id).where(
            WikiPage.campaign_id == campaign_id, WikiPage.slug == slug
        )
        if exclude_page_id is not None:
            stmt = stmt.where(WikiPage.id != exclude_page_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def _require_page(self, page_id: uuid.UUID, db: AsyncSession) -> WikiPage:
        """Fetch a wiki page by id, or raise 404."""
        result = await db.execute(select(WikiPage).where(WikiPage.id == page_id))
        page = result.scalar_one_or_none()
        if page is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Wiki page not found"
            )
        return page

    async def _require_same_campaign(
        self,
        model: type[NPC] | type[Location] | type[Faction],
        entity_id: uuid.UUID,
        campaign_id: uuid.UUID,
        db: AsyncSession,
    ) -> None:
        """Confirm `entity_id` (an NPC/Location/Faction) belongs to `campaign_id`."""
        stmt = select(model.campaign_id).where(model.id == entity_id)
        entity_campaign_id = (await db.execute(stmt)).scalar_one_or_none()
        if entity_campaign_id is None or entity_campaign_id != campaign_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{model.__name__} not found",
            )

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
