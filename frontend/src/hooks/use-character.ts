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
  getCharacterSessions,
  getProficiencyChoices,
  getResourceOptions,
  getSpellAttackProfile,
  getWeaponAttackProfile,
  listCharacters,
  levelUpCharacter,
  removeCharacterEquipment,
  removeCharacterPortrait,
  removeCharacterSpell,
  restCharacter,
  rollDeathSave,
  setCharacterConcentration,
  setProficiencyChoices,
  spendCharacterResource,
  updateCharacterCurrency,
  updateCharacterEquipment,
  updateCharacterHp,
  updateCharacterInfo,
  updateCharacterSpell,
  uploadCharacterPortrait,
} from "@/lib/api/characters";
import type {
  CharacterClassCreate,
  CharacterConcentrationRequest,
  CharacterCreate,
  CharacterCurrencyRequest,
  CharacterDeathSaveRequest,
  CharacterEquipmentCreate,
  CharacterEquipmentUpdate,
  CharacterFeatureCreate,
  CharacterLevelUpRequest,
  CharacterProficiencyChoiceRequest,
  CharacterRestRequest,
  CharacterSpellCastRequest,
  CharacterSpellCreate,
  CharacterSpellUpdate,
  CharacterUpdate,
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

/**
 * The sessions a character has actually appeared in (combat
 * participation), for the ficha's sessions dropdown (Fase 10).
 */
export function useCharacterSessions(characterId: string) {
  return useQuery({
    queryKey: [...CHARACTERS_QUERY_KEY, characterId, "sessions"],
    queryFn: () => getCharacterSessions(characterId),
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

/**
 * Cast a known spell, consuming a spell slot (unless a cantrip or ritual).
 * The response's `save_dc` (saving-throw spells only) and
 * `target_participant_id` let the caller drive the cast UI (Fase 8).
 */
export function useCastCharacterSpell(characterId: string) {
  const queryClient = useQueryClient();
  const queryKey = [...CHARACTERS_QUERY_KEY, characterId];
  return useMutation({
    mutationFn: ({
      spellEntryId,
      data,
    }: {
      spellEntryId: string;
      data: CharacterSpellCastRequest;
    }) => castCharacterSpell(characterId, spellEntryId, data),
    onSuccess: (response) => {
      queryClient.setQueryData(queryKey, response.character);
      void queryClient.invalidateQueries({
        queryKey,
      });
    },
  });
}

/**
 * Take a short or long rest — a long rest restores every spell slot. The
 * response's `hit_dice_rolls` (short rest only) drives the dice-roll
 * animation before the sheet reflects the healed HP (Fase 8).
 */
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
    onSuccess: (response) => {
      queryClient.setQueryData(queryKey, response.character);
    },
    onSettled: () => {
      void queryClient.invalidateQueries({ queryKey });
    },
  });
}

/**
 * Roll a death saving throw — only accepted at 0 hit points. The
 * response's `roll_result` drives the dice-roll animation before the
 * sheet reflects the updated successes/failures (Fase 8).
 */
export function useRollDeathSave(characterId: string) {
  const queryClient = useQueryClient();
  const queryKey = [...CHARACTERS_QUERY_KEY, characterId];
  return useMutation({
    mutationFn: (data: CharacterDeathSaveRequest) => rollDeathSave(characterId, data),
    onSuccess: (response) => {
      queryClient.setQueryData(queryKey, response.character);
      void queryClient.invalidateQueries({ queryKey });
    },
  });
}

/** Start or end concentration on a known spell — `spell_id: null` ends it. */
export function useSetCharacterConcentration(characterId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: CharacterConcentrationRequest) =>
      setCharacterConcentration(characterId, data),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: [...CHARACTERS_QUERY_KEY, characterId],
      });
    },
  });
}

/** Level up a character by one level in one class (existing or new via multiclass). */
export function useLevelUpCharacter(characterId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: CharacterLevelUpRequest) => levelUpCharacter(characterId, data),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: [...CHARACTERS_QUERY_KEY, characterId],
      });
    },
  });
}

/**
 * The character's valid "choose N of [...]" skill proficiency groups
 * (Fase 10), derived from its race/class(es).
 */
export function useProficiencyChoices(characterId: string) {
  return useQuery({
    queryKey: [...CHARACTERS_QUERY_KEY, characterId, "proficiency-choices"],
    queryFn: () => getProficiencyChoices(characterId),
    enabled: Boolean(characterId),
  });
}

/** Mark chosen skills proficient, restricted to the character's valid choice set. */
export function useSetProficiencyChoices(characterId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: CharacterProficiencyChoiceRequest) =>
      setProficiencyChoices(characterId, data),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: [...CHARACTERS_QUERY_KEY, characterId],
      });
    },
  });
}

/**
 * The named options for a class resource (e.g. a Paladin/Cleric's Channel
 * Divinity) — empty when the resource has no option concept for this
 * character (Fase 8).
 */
export function useResourceOptions(characterId: string, resourceKey: string) {
  return useQuery({
    queryKey: [...CHARACTERS_QUERY_KEY, characterId, "resource-options", resourceKey],
    queryFn: () => getResourceOptions(characterId, resourceKey),
    enabled: Boolean(characterId) && Boolean(resourceKey),
  });
}

/** Spend one use of a class resource (rage, ki, ...). */
export function useSpendCharacterResource(characterId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ resourceKey, optionId }: { resourceKey: string; optionId?: string }) =>
      spendCharacterResource(characterId, resourceKey, optionId),
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
 * Resolve an equipped weapon into an attack bonus + damage roll profile.
 * A mutation (not a cached query) since it's triggered by the "Atacar" or
 * "Dano" click itself, right before rolling — see `EquipmentList`.
 */
export function useWeaponAttackProfile(characterId: string) {
  return useMutation({
    mutationFn: (equipmentId: string) =>
      getWeaponAttackProfile(characterId, equipmentId),
  });
}

/**
 * Resolve a known spell into its attack/save + damage roll profile, at
 * whatever level it's cast — same idea as `useWeaponAttackProfile`, see
 * `SpellListByCircle`.
 */
export function useSpellAttackProfile(characterId: string) {
  return useMutation({
    mutationFn: ({
      spellEntryId,
      castAtLevel,
    }: {
      spellEntryId: string;
      castAtLevel?: number;
    }) => getSpellAttackProfile(characterId, spellEntryId, castAtLevel),
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

/**
 * Edit a character's name/alignment/background/ability scores (Fase 10).
 * Unlike `useUpdateCharacterHp` this isn't optimistic — an ability score
 * edit can cascade into AC/max HP/skills recalculated server-side, so the
 * sheet waits for the real response rather than guessing it.
 */
export function useUpdateCharacterInfo(characterId: string) {
  const queryClient = useQueryClient();
  const queryKey = [...CHARACTERS_QUERY_KEY, characterId];

  return useMutation({
    mutationFn: (data: CharacterUpdate) => updateCharacterInfo(characterId, data),
    onSuccess: (character) => {
      queryClient.setQueryData(queryKey, character);
      void queryClient.invalidateQueries({ queryKey });
    },
  });
}

/** Set (or replace) a character's portrait image (Fase 10). Owner only. */
export function useUploadCharacterPortrait(characterId: string) {
  const queryClient = useQueryClient();
  const queryKey = [...CHARACTERS_QUERY_KEY, characterId];

  return useMutation({
    mutationFn: (file: File) => uploadCharacterPortrait(characterId, file),
    onSuccess: (character) => {
      queryClient.setQueryData(queryKey, character);
      void queryClient.invalidateQueries({ queryKey });
    },
  });
}

/** Remove a character's portrait, reverting to the imageless state (Fase 10). Owner only. */
export function useRemoveCharacterPortrait(characterId: string) {
  const queryClient = useQueryClient();
  const queryKey = [...CHARACTERS_QUERY_KEY, characterId];

  return useMutation({
    mutationFn: () => removeCharacterPortrait(characterId),
    onSuccess: (character) => {
      queryClient.setQueryData(queryKey, character);
      void queryClient.invalidateQueries({ queryKey });
    },
  });
}
