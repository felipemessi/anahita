"""HTTP router for the wiki domain."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.core.dependencies import get_current_user
from app.database import get_db
from app.wiki.models import WikiPage, WikiPageLink
from app.wiki.schemas import (
    WikiPageCreate,
    WikiPageLinkCreate,
    WikiPageLinkRead,
    WikiPageRead,
    WikiPageSummary,
    WikiPageUpdate,
)
from app.wiki.service import WikiService

router = APIRouter(tags=["wiki"])

DB = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


def get_wiki_service() -> WikiService:
    """Return a WikiService instance."""
    return WikiService()


WikiSvc = Annotated[WikiService, Depends(get_wiki_service)]


def _to_page_read(page: WikiPage, links: list[WikiPageLink]) -> WikiPageRead:
    """Build the full page response without touching a lazy relationship."""
    return WikiPageRead(
        id=page.id,
        campaign_id=page.campaign_id,
        title=page.title,
        slug=page.slug,
        content=page.content,
        tags=page.tags,
        created_by_id=page.created_by_id,
        created_at=page.created_at,
        links=[WikiPageLinkRead.model_validate(link) for link in links],
    )


@router.post(
    "/campaigns/{campaign_id}/wiki",
    response_model=WikiPageRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_page(
    campaign_id: uuid.UUID,
    body: WikiPageCreate,
    user: CurrentUser,
    db: DB,
    service: WikiSvc,
) -> WikiPageRead:
    """Create a wiki page; only the campaign's DM may do this."""
    page = await service.create_page(campaign_id, user.id, body, db)
    return _to_page_read(page, links=[])


@router.get("/campaigns/{campaign_id}/wiki", response_model=list[WikiPageSummary])
async def list_pages(
    campaign_id: uuid.UUID, user: CurrentUser, db: DB, service: WikiSvc
) -> list[WikiPageSummary]:
    """List a campaign's wiki pages (id/title/tags only)."""
    pages = await service.list_pages(campaign_id, user.id, db)
    return [WikiPageSummary.model_validate(p) for p in pages]


@router.get("/wiki/{page_id}", response_model=WikiPageRead)
async def get_page(
    page_id: uuid.UUID, user: CurrentUser, db: DB, service: WikiSvc
) -> WikiPageRead:
    """Fetch a wiki page's full content and its links."""
    page, links = await service.get_page(page_id, user.id, db)
    return _to_page_read(page, links)


@router.patch("/wiki/{page_id}", response_model=WikiPageRead)
async def update_page(
    page_id: uuid.UUID,
    body: WikiPageUpdate,
    user: CurrentUser,
    db: DB,
    service: WikiSvc,
) -> WikiPageRead:
    """Update a wiki page's title/content/tags. DM-only."""
    await service.update_page(page_id, user.id, body, db)
    page, links = await service.get_page(page_id, user.id, db)
    return _to_page_read(page, links)


@router.delete("/wiki/{page_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_page(
    page_id: uuid.UUID, user: CurrentUser, db: DB, service: WikiSvc
) -> None:
    """Delete a wiki page and its links. DM-only."""
    await service.delete_page(page_id, user.id, db)


@router.post(
    "/wiki/{page_id}/links",
    response_model=WikiPageLinkRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_link(
    page_id: uuid.UUID,
    body: WikiPageLinkCreate,
    user: CurrentUser,
    db: DB,
    service: WikiSvc,
) -> WikiPageLinkRead:
    """Link a wiki page to an NPC, location, or faction. DM-only."""
    link = await service.create_link(page_id, user.id, body, db)
    return WikiPageLinkRead.model_validate(link)


@router.delete(
    "/wiki/{page_id}/links/{link_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_link(
    page_id: uuid.UUID,
    link_id: uuid.UUID,
    user: CurrentUser,
    db: DB,
    service: WikiSvc,
) -> None:
    """Remove a wiki page link. DM-only."""
    await service.delete_link(page_id, link_id, user.id, db)
