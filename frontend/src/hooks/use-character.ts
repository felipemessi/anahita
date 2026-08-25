"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  addCharacterClass,
  addCharacterEquipment,
  addCharacterFeature,
  addCharacterSpell,
  castCharacterSpell,
  createCharacter,
  getCharacter,
  listCharacters,
  removeCharacterEquipment,
  removeCharacterSpell,
  restCharacter,
  rollDeathSave,
  updateCharacterCurrency,
  updateCharacterEquipment,
  updateCharacterHp,
  updateCharacterSpell,
} from "@/lib/api/characters";
import type {
  CharacterClassCreate,
  CharacterCreate,
  CharacterCurrencyRequest,
  CharacterDeathSaveRequest,
  CharacterEquipmentCreate,
  CharacterEquipmentUpdate,
  CharacterFeatureCreate,
  CharacterRestRequest,
  CharacterSpellCastRequest,
  CharacterSpellCreate,
  CharacterSpellUpdate,
} from "@/types/character";

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

/** Add a known/prepared spell to a character. */
export function useAddCharacterSpell(characterId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: CharacterSpellCreate) => addCharacterSpell(characterId, data),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: [...CHARACTERS_QUERY_KEY, characterId],
      });
    },
  });
}

/** Toggle a known spell's `prepared` flag. */
export function useUpdateCharacterSpell(characterId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ spellEntryId, data }: { spellEntryId: string; data: CharacterSpellUpdate }) =>
      updateCharacterSpell(characterId, spellEntryId, data),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: [...CHARACTERS_QUERY_KEY, characterId],
      });
    },
  });
}

/** Forget a known spell. */
export function useRemoveCharacterSpell(characterId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (spellEntryId: string) => removeCharacterSpell(characterId, spellEntryId),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: [...CHARACTERS_QUERY_KEY, characterId],
      });
    },
  });
}

/** Cast a known spell, consuming a spell slot (unless a cantrip or ritual). */
export function useCastCharacterSpell(characterId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      spellEntryId,
      data,
    }: {
      spellEntryId: string;
      data: CharacterSpellCastRequest;
    }) => castCharacterSpell(characterId, spellEntryId, data),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: [...CHARACTERS_QUERY_KEY, characterId],
      });
    },
  });
}

/** Take a short or long rest — a long rest restores every spell slot. */
export function useRestCharacter(characterId: string) {
  const queryClient = useQueryClient();
  const queryKey = [...CHARACTERS_QUERY_KEY, characterId];

  return useMutation({
    mutationFn: (data: CharacterRestRequest) => restCharacter(characterId, data),
    onMutate: async (data: CharacterRestRequest) => {
      await queryClient.cancelQueries({ queryKey });
      const previous = queryClient.getQueryData(queryKey);
      if (data.rest_type === "long") {
        queryClient.setQueryData(queryKey, (current: unknown) => {
          if (!current || typeof current !== "object" || !("spell_slots" in current)) {
            return current;
          }
          const slots = (current as { spell_slots: { used: number }[] }).spell_slots;
          return { ...current, spell_slots: slots.map((s) => ({ ...s, used: 0 })) };
        });
      }
      return { previous };
    },
    onError: (_err, _data, context) => {
      if (context?.previous !== undefined) {
        queryClient.setQueryData(queryKey, context.previous);
      }
    },
    onSettled: () => {
      void queryClient.invalidateQueries({ queryKey });
    },
  });
}

/** Roll a death saving throw — only accepted at 0 hit points. */
export function useRollDeathSave(characterId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: CharacterDeathSaveRequest) => rollDeathSave(characterId, data),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: [...CHARACTERS_QUERY_KEY, characterId],
      });
    },
  });
}

/** Add an item to a character's personal inventory. */
export function useAddCharacterEquipment(characterId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: CharacterEquipmentCreate) =>
      addCharacterEquipment(characterId, data),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: [...CHARACTERS_QUERY_KEY, characterId],
      });
    },
  });
}

/** Edit an inventory item (equipped/attunement/quantity). */
export function useUpdateCharacterEquipment(characterId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      equipmentId,
      data,
    }: {
      equipmentId: string;
      data: CharacterEquipmentUpdate;
    }) => updateCharacterEquipment(characterId, equipmentId, data),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: [...CHARACTERS_QUERY_KEY, characterId],
      });
    },
  });
}

/** Remove an item from a character's inventory. */
export function useRemoveCharacterEquipment(characterId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (equipmentId: string) => removeCharacterEquipment(characterId, equipmentId),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: [...CHARACTERS_QUERY_KEY, characterId],
      });
    },
  });
}

/**
 * Record a currency gain/spend with an optimistic update — reverts (e.g.
 * insufficient funds, 422) via `onError`.
 */
export function useUpdateCharacterCurrency(characterId: string) {
  const queryClient = useQueryClient();
  const queryKey = [...CHARACTERS_QUERY_KEY, characterId];

  return useMutation({
    mutationFn: (data: CharacterCurrencyRequest) =>
      updateCharacterCurrency(characterId, data),
    onMutate: async (data: CharacterCurrencyRequest) => {
      await queryClient.cancelQueries({ queryKey });
      const previous = queryClient.getQueryData(queryKey);
      queryClient.setQueryData(queryKey, (current: unknown) =>
        current && typeof current === "object" && "currency_cp" in current
          ? {
              ...current,
              currency_cp: (current as { currency_cp: number }).currency_cp + data.delta,
            }
          : current,
      );
      return { previous };
    },
    onError: (_err, _data, context) => {
      if (context?.previous !== undefined) {
        queryClient.setQueryData(queryKey, context.previous);
      }
    },
    onSettled: () => {
      void queryClient.invalidateQueries({ queryKey });
    },
  });
}

/** Record a class/feat feature on a character. */
export function useAddCharacterFeature(characterId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: CharacterFeatureCreate) => addCharacterFeature(characterId, data),
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
