/**
 * PROVISIONAL — the backend `inventory` domain (Fase 4) does not exist yet,
 * so there is no schemas.py to mirror. Shapes here follow
 * docs/anahita-backend-prd.md §7.9. Re-verify against the real Pydantic
 * schemas once the backend domain ships.
 */

export interface PartyInventoryEntry {
  id: string;
  campaign_id: string;
  item_id: string;
  quantity: number;
  notes: string | null;
}

export interface LootDrop {
  id: string;
  encounter_id: string;
  /** null for custom (non-catalog) items — see `custom_item_name`. */
  item_id: string | null;
  custom_item_name: string | null;
  quantity: number;
  /** All currency converted to copper pieces. */
  currency_cp: number;
  /** Character id, if claimed. */
  claimed_by: string | null;
}
