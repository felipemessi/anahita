"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  addCharacterClass,
  createCharacter,
  getCharacter,
  listCharacters,
  updateCharacterHp,
} from "@/lib/api/characters";
import type { CharacterClassCreate, CharacterCreate } from "@/types/character";

export const CHARACTERS_QUERY_KEY = ["characters"] as const;

/** Every character in a campaign. */
export function useCharacters(campaignId: string) {
  return useQuery({
    queryKey: [...CHARACTERS_QUERY_KEY, "by-campaign", campaignId],
    queryFn: () => listCharacters(campaignId),
    enabled: Boolean(campaignId),
  });
}

/** A single character's sheet, with calculated modifiers/bonuses. */
export function useCharacter(characterId: string) {
  return useQuery({
    queryKey: [...CHARACTERS_QUERY_KEY, characterId],
    queryFn: () => getCharacter(characterId),
    enabled: Boolean(characterId),
  });
}

/** Create a character sheet. */
export function useCreateCharacter() {
  return useMutation({
    mutationFn: (data: CharacterCreate) => createCharacter(data),
  });
}

/** Add a class to a character (multiclass). */
export function useAddCharacterClass(characterId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: CharacterClassCreate) => addCharacterClass(characterId, data),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: [...CHARACTERS_QUERY_KEY, characterId],
      });
    },
  });
}

/**
 * Update HP with an optimistic update: the cache reflects the new value
 * immediately and rolls back if the request fails.
 */
export function useUpdateCharacterHp(characterId: string) {
  const queryClient = useQueryClient();
  const queryKey = [...CHARACTERS_QUERY_KEY, characterId];

  return useMutation({
    mutationFn: (hitPointCurrent: number) =>
      updateCharacterHp(characterId, hitPointCurrent),
    onMutate: async (hitPointCurrent: number) => {
      await queryClient.cancelQueries({ queryKey });
      const previous = queryClient.getQueryData(queryKey);
      queryClient.setQueryData(queryKey, (current: unknown) =>
        current && typeof current === "object"
          ? { ...current, hit_point_current: hitPointCurrent }
          : current,
      );
      return { previous };
    },
    onError: (_err, _hitPointCurrent, context) => {
      if (context?.previous !== undefined) {
        queryClient.setQueryData(queryKey, context.previous);
      }
    },
    onSettled: () => {
      void queryClient.invalidateQueries({ queryKey });
    },
  });
}
