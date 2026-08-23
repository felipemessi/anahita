import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import React from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const updateCharacterHp = vi.fn();
vi.mock("@/lib/api/characters", () => ({
  updateCharacterHp: (...args: unknown[]) => updateCharacterHp(...args),
}));

import { CHARACTERS_QUERY_KEY, useUpdateCharacterHp } from "./use-character";

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
  ability_scores: [],
  skills: [],
  classes: [],
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
