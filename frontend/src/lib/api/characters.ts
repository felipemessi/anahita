import { apiFetch } from "@/lib/api/client";
import type { Character, CharacterClassCreate, CharacterCreate } from "@/types/character";

/** Calls the characters endpoints exposed by backend/app/characters/router.py. */

/** List every character in a campaign. Viewable by any of its members. */
export function listCharacters(campaignId: string): Promise<Character[]> {
  return apiFetch<Character[]>(
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
