import { apiFetch } from "@/lib/api/client";
import type { Feature } from "@/types/catalog";
import type { GameSession } from "@/types/session";
import type {
  Character,
  CharacterClassCreate,
  CharacterConcentrationRequest,
  CharacterCreate,
  CharacterCurrencyRequest,
  CharacterDeathSaveRequest,
  CharacterDeathSaveResponse,
  CharacterEquipmentCreate,
  CharacterEquipmentUpdate,
  CharacterFeatureCreate,
  CharacterLevelUpRequest,
  CharacterRestRequest,
  CharacterRestResponse,
  CharacterSpellCastRequest,
  CharacterSpellCastResponse,
  CharacterSpellCreate,
  CharacterSpellUpdate,
  CharacterSummary,
  CharacterUpdate,
  SpellAttackProfile,
  WeaponAttackProfile,
} from "@/types/character";

/** Calls the characters endpoints exposed by backend/app/characters/router.py. */

/**
 * List every character in a campaign. Viewable by any of its members — the
 * owner and the DM get the full sheet, everyone else a `CharacterSummary`.
 */
export function listCharacters(
  campaignId: string,
): Promise<(Character | CharacterSummary)[]> {
  return apiFetch<(Character | CharacterSummary)[]>(
    `/characters?campaign_id=${encodeURIComponent(campaignId)}`,
  );
}

/** Create a character sheet for the authenticated user's own campaign membership. */
export function createCharacter(data: CharacterCreate): Promise<Character> {
  return apiFetch<Character>("/characters", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/** Fetch a character sheet with calculated modifiers and skill bonuses. */
export function getCharacter(characterId: string): Promise<Character> {
  return apiFetch<Character>(`/characters/${characterId}`);
}

/**
 * List the sessions a character has actually appeared in (combat
 * participation), for the ficha's sessions dropdown (Fase 10). Derived
 * server-side, not an explicit list — respects the character's own saved
 * display order when one exists.
 */
export function getCharacterSessions(characterId: string): Promise<GameSession[]> {
  return apiFetch<GameSession[]>(`/characters/${characterId}/sessions`);
}

/** Add a class to a character, enabling multiclass. */
export function addCharacterClass(
  characterId: string,
  data: CharacterClassCreate,
): Promise<Character> {
  return apiFetch<Character>(`/characters/${characterId}/classes`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/** Update a character's current HP. */
export function updateCharacterHp(
  characterId: string,
  hitPointCurrent: number,
): Promise<Character> {
  return apiFetch<Character>(`/characters/${characterId}`, {
    method: "PATCH",
    body: JSON.stringify({ hit_point_current: hitPointCurrent }),
  });
}

/**
 * Edit a character's name/alignment/background/ability scores post-creation
 * (Fase 10) — distinct from `updateCharacterHp`. `ability_scores` is
 * partial: send only the abilities being changed. Race/class are locked.
 */
export function updateCharacterInfo(
  characterId: string,
  data: CharacterUpdate,
): Promise<Character> {
  return apiFetch<Character>(`/characters/${characterId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

/** Add a known/prepared spell to a character. */
export function addCharacterSpell(
  characterId: string,
  data: CharacterSpellCreate,
): Promise<Character> {
  return apiFetch<Character>(`/characters/${characterId}/spells`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/** Toggle a known spell's `prepared` flag. */
export function updateCharacterSpell(
  characterId: string,
  spellEntryId: string,
  data: CharacterSpellUpdate,
): Promise<Character> {
  return apiFetch<Character>(`/characters/${characterId}/spells/${spellEntryId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

/** Forget a known spell. */
export function removeCharacterSpell(
  characterId: string,
  spellEntryId: string,
): Promise<Character> {
  return apiFetch<Character>(`/characters/${characterId}/spells/${spellEntryId}`, {
    method: "DELETE",
  });
}

/** Cast a known spell, consuming a spell slot (unless a cantrip or ritual). */
export function castCharacterSpell(
  characterId: string,
  spellEntryId: string,
  data: CharacterSpellCastRequest,
): Promise<CharacterSpellCastResponse> {
  return apiFetch<CharacterSpellCastResponse>(
    `/characters/${characterId}/spells/${spellEntryId}/cast`,
    {
      method: "POST",
      body: JSON.stringify(data),
    },
  );
}

/** Resolve a known spell into its attack/save + damage roll profile. */
export function getSpellAttackProfile(
  characterId: string,
  spellEntryId: string,
  castAtLevel?: number,
): Promise<SpellAttackProfile> {
  const query = castAtLevel != null ? `?cast_at_level=${castAtLevel}` : "";
  return apiFetch<SpellAttackProfile>(
    `/characters/${characterId}/spells/${spellEntryId}/attack-profile${query}`,
  );
}

/** Take a short or long rest — a long rest restores every spell slot. */
export function restCharacter(
  characterId: string,
  data: CharacterRestRequest,
): Promise<CharacterRestResponse> {
  return apiFetch<CharacterRestResponse>(`/characters/${characterId}/rest`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/** Roll a death saving throw — only accepted at 0 hit points. */
export function rollDeathSave(
  characterId: string,
  data: CharacterDeathSaveRequest,
): Promise<CharacterDeathSaveResponse> {
  return apiFetch<CharacterDeathSaveResponse>(`/characters/${characterId}/death-save`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/** Level up a character by one level in one class (existing or new via multiclass). */
export function levelUpCharacter(
  characterId: string,
  data: CharacterLevelUpRequest,
): Promise<Character> {
  return apiFetch<Character>(`/characters/${characterId}/level-up`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/** Start or end concentration on a known spell — `spell_id: null` ends it. */
export function setCharacterConcentration(
  characterId: string,
  data: CharacterConcentrationRequest,
): Promise<Character> {
  return apiFetch<Character>(`/characters/${characterId}/concentration`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/**
 * List the named options for a class resource (e.g. a Paladin/Cleric's
 * Channel Divinity) — empty when the resource has no option concept, or
 * matches none of the character's classes (Fase 8).
 */
export function getResourceOptions(
  characterId: string,
  resourceKey: string,
): Promise<Feature[]> {
  return apiFetch<Feature[]>(
    `/characters/${characterId}/resources/${encodeURIComponent(resourceKey)}/options`,
  );
}

/** Spend one use of a class resource (rage, ki, ...). */
export function spendCharacterResource(
  characterId: string,
  resourceKey: string,
  optionId?: string,
): Promise<Character> {
  const query = optionId ? `?option_id=${encodeURIComponent(optionId)}` : "";
  return apiFetch<Character>(
    `/characters/${characterId}/resources/${encodeURIComponent(resourceKey)}/use${query}`,
    { method: "POST" },
  );
}

/** Add an item to a character's personal inventory. */
export function addCharacterEquipment(
  characterId: string,
  data: CharacterEquipmentCreate,
): Promise<Character> {
  return apiFetch<Character>(`/characters/${characterId}/equipment`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/** Edit an inventory item (equipped/attunement/quantity). */
export function updateCharacterEquipment(
  characterId: string,
  equipmentId: string,
  data: CharacterEquipmentUpdate,
): Promise<Character> {
  return apiFetch<Character>(`/characters/${characterId}/equipment/${equipmentId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

/** Remove an item from a character's inventory. */
export function removeCharacterEquipment(
  characterId: string,
  equipmentId: string,
): Promise<Character> {
  return apiFetch<Character>(`/characters/${characterId}/equipment/${equipmentId}`, {
    method: "DELETE",
  });
}

/** Resolve an equipped weapon into an attack bonus + damage roll profile. */
export function getWeaponAttackProfile(
  characterId: string,
  equipmentId: string,
): Promise<WeaponAttackProfile> {
  return apiFetch<WeaponAttackProfile>(
    `/characters/${characterId}/equipment/${equipmentId}/attack-profile`,
  );
}

/** Record a currency gain (positive delta) or spend (negative). */
export function updateCharacterCurrency(
  characterId: string,
  data: CharacterCurrencyRequest,
): Promise<Character> {
  return apiFetch<Character>(`/characters/${characterId}/currency`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/**
 * Set (or replace) a character's portrait image. Owner only. Sent as
 * `multipart/form-data`, same pattern as `createHandout` — see
 * backend/app/characters/router.py.
 */
export function uploadCharacterPortrait(
  characterId: string,
  file: File,
): Promise<Character> {
  const form = new FormData();
  form.append("file", file);

  return apiFetch<Character>(`/characters/${characterId}/portrait`, {
    method: "POST",
    body: form,
  });
}

/** Remove a character's portrait, reverting to the imageless state. Owner only. */
export function removeCharacterPortrait(characterId: string): Promise<Character> {
  return apiFetch<Character>(`/characters/${characterId}/portrait`, {
    method: "DELETE",
  });
}

/** Record a class/feat feature on a character. */
export function addCharacterFeature(
  characterId: string,
  data: CharacterFeatureCreate,
): Promise<Character> {
  return apiFetch<Character>(`/characters/${characterId}/features`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}
