"use client";

import { useQuery } from "@tanstack/react-query";

import { listUsersByIds } from "@/lib/api/users";

/** Public profiles (username/email) for a batch of user ids. */
export function useUserProfiles(ids: string[]) {
  return useQuery({
    queryKey: ["users", "by-ids", [...ids].sort()],
    queryFn: () => listUsersByIds(ids),
    enabled: ids.length > 0,
  });
}
