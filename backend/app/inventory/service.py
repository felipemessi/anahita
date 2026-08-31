"""InventoryService orchestrates the party inventory and encounter loot drops."""

import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.campaigns.domain import CampaignRole
from app.campaigns.models import CampaignMember
from app.catalog.models import Item, MagicItem
from app.characters.models import Character, CharacterEquipment
from app.combat.models import Encounter
from app.inventory.domain import LootDropKindError, validate_loot_drop_kind
from app.inventory.models import LootDrop, PartyInventory
from app.inventory.schemas import (
    LootDropCreate,
    LootDropRead,
    PartyInventoryCreate,
    PartyInventoryRead,
    PartyInventoryUpdate,
)
from app.sessions.models import Session


class InventoryService:
    """Orchestrates PartyInventory CRUD and LootDrop distribution/claiming."""

    async def add_to_inventory(
        self,
        campaign_id: uuid.UUID,
        requester_id: uuid.UUID,
        data: PartyInventoryCreate,
        db: AsyncSession,
    ) -> PartyInventoryRead:
        """Add a stack of an item to the party inventory. DM only."""
        await self._require_dm(campaign_id, requester_id, db)
        await self._require_visible_item(campaign_id, data.item_id, db)

        entry = PartyInventory(
            campaign_id=campaign_id,
            item_id=data.item_id,
            quantity=data.quantity,
            notes=data.notes,
        )
        db.add(entry)
        await db.commit()
        await db.refresh(entry)
        return PartyInventoryRead.model_validate(entry)

    async def list_inventory(
        self, campaign_id: uuid.UUID, requester_id: uuid.UUID, db: AsyncSession
    ) -> list[PartyInventoryRead]:
        """List a campaign's party inventory. Viewable by any campaign member."""
        await self._require_membership(campaign_id, requester_id, db)
        result = await db.execute(
            select(PartyInventory).where(PartyInventory.campaign_id == campaign_id)
        )
        return [PartyInventoryRead.model_validate(e) for e in result.scalars().all()]

    async def update_inventory_entry(
        self,
        campaign_id: uuid.UUID,
        entry_id: uuid.UUID,
        requester_id: uuid.UUID,
        data: PartyInventoryUpdate,
        db: AsyncSession,
    ) -> PartyInventoryRead:
        """Update a party inventory entry's quantity/notes. DM only."""
        await self._require_dm(campaign_id, requester_id, db)
        entry = await self._load_inventory_entry_or_404(campaign_id, entry_id, db)

        if data.quantity is not None:
            entry.quantity = data.quantity
        if data.notes is not None:
            entry.notes = data.notes
        await db.commit()
        await db.refresh(entry)
        return PartyInventoryRead.model_validate(entry)

    async def remove_from_inventory(
        self,
        campaign_id: uuid.UUID,
        entry_id: uuid.UUID,
        requester_id: uuid.UUID,
        db: AsyncSession,
    ) -> None:
        """Remove a party inventory entry entirely. DM only."""
        await self._require_dm(campaign_id, requester_id, db)
        entry = await self._load_inventory_entry_or_404(campaign_id, entry_id, db)
        await db.delete(entry)
        await db.commit()

    async def create_loot_drop(
        self,
        encounter_id: uuid.UUID,
        requester_id: uuid.UUID,
        data: LootDropCreate,
        db: AsyncSession,
    ) -> LootDropRead:
        """Record a loot drop (catalog/magic/custom item and/or currency). DM only."""
        encounter, session = await self._load_encounter_and_session(encounter_id, db)
        await self._require_dm(session.campaign_id, requester_id, db)

        try:
            validate_loot_drop_kind(
                item_id=data.item_id,
                magic_item_id=data.magic_item_id,
                custom_item_name=data.custom_item_name,
                currency_cp=data.currency_cp,
            )
        except LootDropKindError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
            ) from exc
        if data.item_id is not None:
            await self._require_visible_item(session.campaign_id, data.item_id, db)
        if data.magic_item_id is not None:
            await self._require_visible_magic_item(
                session.campaign_id, data.magic_item_id, db
            )

        drop = LootDrop(
            encounter_id=encounter.id,
            item_id=data.item_id,
            magic_item_id=data.magic_item_id,
            custom_item_name=data.custom_item_name,
            quantity=data.quantity,
            currency_cp=data.currency_cp,
        )
        db.add(drop)
        await db.commit()
        await db.refresh(drop)
        return LootDropRead.model_validate(drop)

    async def list_loot_drops(
        self, encounter_id: uuid.UUID, requester_id: uuid.UUID, db: AsyncSession
    ) -> list[LootDropRead]:
        """List an encounter's loot drops. Viewable by any campaign member."""
        _encounter, session = await self._load_encounter_and_session(encounter_id, db)
        await self._require_membership(session.campaign_id, requester_id, db)
        result = await db.execute(
            select(LootDrop).where(LootDrop.encounter_id == encounter_id)
        )
        return [LootDropRead.model_validate(d) for d in result.scalars().all()]

    async def claim_loot_drop(
        self,
        loot_drop_id: uuid.UUID,
        requester_id: uuid.UUID,
        character_id: uuid.UUID,
        db: AsyncSession,
    ) -> LootDropRead:
        """Claim a loot drop for a character, adding it to their inventory.

        Allowed for the character's own player, or the campaign's DM acting
        on behalf of any character in the campaign (`_require_owner_or_dm`
        below enforces "own character or DM").

        The claimed item (catalog, magic, or custom — `LootDrop`'s three
        mutually-exclusive kinds, see `app.inventory.domain.
        validate_loot_drop_kind`) is merged into a matching
        `CharacterEquipment` entry if one already exists, or created
        otherwise. A pure-currency drop (no item) has nothing to add to the
        equipment list.
        """
        result = await db.execute(select(LootDrop).where(LootDrop.id == loot_drop_id))
        drop = result.scalar_one_or_none()
        if drop is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Loot drop not found"
            )
        if drop.claimed_by is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Loot drop already claimed",
            )
        _encounter, session = await self._load_encounter_and_session(
            drop.encounter_id, db
        )
        character = await self._require_character_in_campaign(
            session.campaign_id, character_id, db
        )
        await self._require_owner_or_dm(
            session.campaign_id, character, requester_id, db
        )

        drop.claimed_by = character.id
        await self._add_loot_to_equipment(character.id, drop, db)
        await db.commit()
        await db.refresh(drop)
        return LootDropRead.model_validate(drop)

    async def _add_loot_to_equipment(
        self, character_id: uuid.UUID, drop: LootDrop, db: AsyncSession
    ) -> None:
        """Merge/create the `CharacterEquipment` entry for a claimed loot drop.

        `LootDrop` guarantees at most one of `item_id`/`magic_item_id`/
        `custom_item_name` is set (`validate_loot_drop_kind`), so a pure
        currency drop with none of the three simply does nothing here.
        """
        if drop.item_id is not None:
            match = select(CharacterEquipment).where(
                CharacterEquipment.character_id == character_id,
                CharacterEquipment.item_id == drop.item_id,
                CharacterEquipment.magic_item_id.is_(None),
                CharacterEquipment.custom_item_name.is_(None),
            )
        elif drop.magic_item_id is not None:
            match = select(CharacterEquipment).where(
                CharacterEquipment.character_id == character_id,
                CharacterEquipment.magic_item_id == drop.magic_item_id,
            )
        elif drop.custom_item_name is not None:
            match = select(CharacterEquipment).where(
                CharacterEquipment.character_id == character_id,
                CharacterEquipment.custom_item_name == drop.custom_item_name,
                CharacterEquipment.item_id.is_(None),
                CharacterEquipment.magic_item_id.is_(None),
            )
        else:
            return

        result = await db.execute(match)
        existing = result.scalar_one_or_none()
        if existing is not None:
            existing.quantity += drop.quantity
            return

        db.add(
            CharacterEquipment(
                character_id=character_id,
                item_id=drop.item_id,
                magic_item_id=drop.magic_item_id,
                custom_item_name=drop.custom_item_name,
                quantity=drop.quantity,
            )
        )

    async def _load_inventory_entry_or_404(
        self, campaign_id: uuid.UUID, entry_id: uuid.UUID, db: AsyncSession
    ) -> PartyInventory:
        result = await db.execute(
            select(PartyInventory).where(
                PartyInventory.id == entry_id,
                PartyInventory.campaign_id == campaign_id,
            )
        )
        entry = result.scalar_one_or_none()
        if entry is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Inventory entry not found",
            )
        return entry

    async def _load_encounter_and_session(
        self, encounter_id: uuid.UUID, db: AsyncSession
    ) -> tuple[Encounter, Session]:
        result = await db.execute(select(Encounter).where(Encounter.id == encounter_id))
        encounter = result.scalar_one_or_none()
        if encounter is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Encounter not found"
            )
        session_result = await db.execute(
            select(Session).where(Session.id == encounter.session_id)
        )
        session = session_result.scalar_one_or_none()
        if session is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
            )
        return encounter, session

    async def _require_character_in_campaign(
        self, campaign_id: uuid.UUID, character_id: uuid.UUID, db: AsyncSession
    ) -> Character:
        result = await db.execute(
            select(Character)
            .join(CampaignMember, CampaignMember.id == Character.campaign_member_id)
            .where(
                Character.id == character_id,
                CampaignMember.campaign_id == campaign_id,
            )
        )
        character = result.scalar_one_or_none()
        if character is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Character not found"
            )
        return character

    async def _require_owner_or_dm(
        self,
        campaign_id: uuid.UUID,
        character: Character,
        requester_id: uuid.UUID,
        db: AsyncSession,
    ) -> None:
        member = await self._require_membership(campaign_id, requester_id, db)
        if member.role == CampaignRole.dm:
            return
        char_member_result = await db.execute(
            select(CampaignMember).where(
                CampaignMember.id == character.campaign_member_id
            )
        )
        char_member = char_member_result.scalar_one()
        if char_member.user_id != requester_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot claim loot for someone else's character",
            )

    async def _require_visible_item(
        self, campaign_id: uuid.UUID, item_id: uuid.UUID, db: AsyncSession
    ) -> Item:
        """Fetch an item usable in this campaign: SRD, or this campaign's homebrew."""
        result = await db.execute(select(Item).where(Item.id == item_id))
        item = result.scalar_one_or_none()
        if item is None or (item.is_custom and item.campaign_id != campaign_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Item not found"
            )
        return item

    async def _require_visible_magic_item(
        self, campaign_id: uuid.UUID, magic_item_id: uuid.UUID, db: AsyncSession
    ) -> MagicItem:
        """Fetch a magic item usable here: SRD, or this campaign's homebrew."""
        result = await db.execute(
            select(MagicItem).where(MagicItem.id == magic_item_id)
        )
        magic_item = result.scalar_one_or_none()
        if magic_item is None or (
            magic_item.is_custom and magic_item.campaign_id != campaign_id
        ):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Magic item not found"
            )
        return magic_item

    async def _require_membership(
        self, campaign_id: uuid.UUID, requester_id: uuid.UUID, db: AsyncSession
    ) -> CampaignMember:
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
        member = await self._require_membership(campaign_id, requester_id, db)
        if member.role != CampaignRole.dm:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the campaign's DM can manage the inventory",
            )
        return member
