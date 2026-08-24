/**
 * Mirrors backend/app/inventory/schemas.py (PRD §7.9).
 */

export interface PartyInventoryEntry {
  id: string;
  campaign_id: string;
  item_id: string;
  quantity: number;
  notes: string | null;
}

export interface PartyInventoryCreate {
  item_id: string;
  quantity?: number;
  notes?: string | null;
}

export interface PartyInventoryUpdate {
  quantity?: number;
  notes?: string | null;
}

export interface LootDrop {
  id: string;
  encounter_id: string;
  /** null unless this drop is a catalog item — see `magic_item_id`/`custom_item_name`. */
  item_id: string | null;
  /** null unless this drop is a magic item. */
  magic_item_id: string | null;
  /** null unless this drop is a free-text (non-catalog) item. */
  custom_item_name: string | null;
  quantity: number;
  /** All currency converted to copper pieces. */
  currency_cp: number;
  /** Character id, if claimed. */
  claimed_by: string | null;
}

/** `item_id`, `magic_item_id`, and `custom_item_name` are mutually exclusive. */
export interface LootDropCreate {
  item_id?: string | null;
  magic_item_id?: string | null;
  custom_item_name?: string | null;
  quantity?: number;
  currency_cp?: number;
}

export interface LootDropClaim {
  character_id: string;
}
