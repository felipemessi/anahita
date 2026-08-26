import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import React from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const updateCharacterHp = vi.fn();
const restCharacter = vi.fn();
const updateCharacterCurrency = vi.fn();
const updateCharacterEquipment = vi.fn();
const getCharacter = vi.fn();
vi.mock("@/lib/api/characters", () => ({
  updateCharacterHp: (...args: unknown[]) => updateCharacterHp(...args),
  restCharacter: (...args: unknown[]) => restCharacter(...args),
  updateCharacterCurrency: (...args: unknown[]) => updateCharacterCurrency(...args),
  updateCharacterEquipment: (...args: unknown[]) => updateCharacterEquipment(...args),
  getCharacter: (...args: unknown[]) => getCharacter(...args),
}));

import {
  CHARACTERS_QUERY_KEY,
  useCharacter,
  useRestCharacter,
  useUpdateCharacterCurrency,
  useUpdateCharacterEquipment,
  useUpdateCharacterHp,
} from "./use-character";

const character = {
  id: "char-1",
  campaign_member_id: "mem-1",
  name: "Aria",
  race_id: "race-1",
  subrace_id: null,
  level: 1,
  experience_points: 0,
  alignment: null,
  background: null,
  hit_point_max: 20,
  hit_point_current: 20,
  temporary_hit_points: 0,
  armor_class: 14,
  speed: 30,
  inspiration: false,
  proficiency_bonus: 2,
  currency_cp: 500,
  ability_scores: [],
  skills: [],
  classes: [],
  spells: [],
  spell_slots: [
    { spell_level: 1, used: 2, max: 2 },
    { spell_level: 2, used: 1, max: 1 },
  ],
  equipment: [],
  features: [],
};

function setup() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  queryClient.setQueryData([...CHARACTERS_QUERY_KEY, "char-1"], character);

  const wrapper = ({ children }: { children: React.ReactNode }) =>
    React.createElement(QueryClientProvider, { client: queryClient }, children);

  return { queryClient, wrapper };
}

describe("useUpdateCharacterHp", () => {
  beforeEach(() => {
    updateCharacterHp.mockReset();
  });

  it("updates the cache optimistically, before the request resolves", async () => {
    let resolveRequest!: (value: typeof character) => void;
    updateCharacterHp.mockReturnValue(
      new Promise((resolve) => {
        resolveRequest = resolve;
      }),
    );

    const { queryClient, wrapper } = setup();
    const { result } = renderHook(() => useUpdateCharacterHp("char-1"), { wrapper });

    result.current.mutate(12);

    await waitFor(() => {
      expect(
        queryClient.getQueryData<typeof character>([...CHARACTERS_QUERY_KEY, "char-1"])
          ?.hit_point_current,
      ).toBe(12);
    });

    resolveRequest({ ...character, hit_point_current: 12 });
  });

  it("rolls back the cache when the request fails", async () => {
    updateCharacterHp.mockRejectedValueOnce(new Error("network error"));

    const { queryClient, wrapper } = setup();
    const { result } = renderHook(() => useUpdateCharacterHp("char-1"), { wrapper });

    result.current.mutate(12);

    await waitFor(() => {
      expect(
        queryClient.getQueryData<typeof character>([...CHARACTERS_QUERY_KEY, "char-1"])
          ?.hit_point_current,
      ).toBe(20);
    });
  });
});

describe("useRestCharacter", () => {
  beforeEach(() => {
    restCharacter.mockReset();
  });

  it("optimistically zeroes every spell slot's used count on a long rest", async () => {
    let resolveRequest!: (value: {
      character: typeof character;
      hit_dice_rolls: unknown[];
    }) => void;
    restCharacter.mockReturnValue(
      new Promise((resolve) => {
        resolveRequest = resolve;
      }),
    );

    const { queryClient, wrapper } = setup();
    const { result } = renderHook(() => useRestCharacter("char-1"), { wrapper });

    result.current.mutate({ rest_type: "long" });

    await waitFor(() => {
      const cached = queryClient.getQueryData<typeof character>([
        ...CHARACTERS_QUERY_KEY,
        "char-1",
      ]);
      expect(cached?.spell_slots.every((s) => s.used === 0)).toBe(true);
    });

    resolveRequest({
      character: {
        ...character,
        spell_slots: character.spell_slots.map((s) => ({ ...s, used: 0 })),
      },
      hit_dice_rolls: [],
    });
  });

  it("leaves spell slots untouched on a short rest", async () => {
    restCharacter.mockResolvedValue({ character, hit_dice_rolls: [] });
    const { queryClient, wrapper } = setup();
    const { result } = renderHook(() => useRestCharacter("char-1"), { wrapper });

    result.current.mutate({ rest_type: "short" });

    await waitFor(() => expect(restCharacter).toHaveBeenCalled());
    const cached = queryClient.getQueryData<typeof character>([
      ...CHARACTERS_QUERY_KEY,
      "char-1",
    ]);
    expect(cached?.spell_slots[0]?.used).toBe(2);
  });

  it("rolls back spell slots when the long rest request fails", async () => {
    restCharacter.mockRejectedValueOnce(new Error("network error"));

    const { queryClient, wrapper } = setup();
    const { result } = renderHook(() => useRestCharacter("char-1"), { wrapper });

    result.current.mutate({ rest_type: "long" });

    await waitFor(() => {
      const cached = queryClient.getQueryData<typeof character>([
        ...CHARACTERS_QUERY_KEY,
        "char-1",
      ]);
      expect(cached?.spell_slots[0]?.used).toBe(2);
    });
  });
});

describe("useUpdateCharacterCurrency", () => {
  beforeEach(() => {
    updateCharacterCurrency.mockReset();
  });

  it("updates the cached balance optimistically", async () => {
    let resolveRequest!: (value: typeof character) => void;
    updateCharacterCurrency.mockReturnValue(
      new Promise((resolve) => {
        resolveRequest = resolve;
      }),
    );

    const { queryClient, wrapper } = setup();
    const { result } = renderHook(() => useUpdateCharacterCurrency("char-1"), { wrapper });

    result.current.mutate({ delta: -100 });

    await waitFor(() => {
      const cached = queryClient.getQueryData<typeof character>([
        ...CHARACTERS_QUERY_KEY,
        "char-1",
      ]);
      expect(cached?.currency_cp).toBe(400);
    });

    resolveRequest({ ...character, currency_cp: 400 });
  });

  it("rolls back the balance when the spend is rejected (insufficient funds)", async () => {
    updateCharacterCurrency.mockRejectedValueOnce(new Error("422"));

    const { queryClient, wrapper } = setup();
    const { result } = renderHook(() => useUpdateCharacterCurrency("char-1"), { wrapper });

    result.current.mutate({ delta: -1000 });

    await waitFor(() => {
      const cached = queryClient.getQueryData<typeof character>([
        ...CHARACTERS_QUERY_KEY,
        "char-1",
      ]);
      expect(cached?.currency_cp).toBe(500);
    });
  });
});

describe("useUpdateCharacterEquipment", () => {
  beforeEach(() => {
    updateCharacterEquipment.mockReset();
    getCharacter.mockReset();
  });

  it("toggling equipped invalidates the character query, so armor_class reflects the server's recalculated value", async () => {
    updateCharacterEquipment.mockResolvedValue(undefined);
    getCharacter.mockResolvedValue({ ...character, armor_class: 16 });

    const { wrapper } = setup();
    const { result: characterResult } = renderHook(() => useCharacter("char-1"), { wrapper });
    const { result: updateResult } = renderHook(
      () => useUpdateCharacterEquipment("char-1"),
      { wrapper },
    );

    expect(characterResult.current.data?.armor_class).toBe(14);

    updateResult.current.mutate({ equipmentId: "eq-1", data: { equipped: true } });

    await waitFor(() => expect(characterResult.current.data?.armor_class).toBe(16));
  });
});
