import { beforeEach, describe, expect, it, vi } from "vitest";

const apiFetch = vi.fn();
const setAccessToken = vi.fn();
vi.mock("@/lib/api/client", () => ({
  apiFetch: (...args: unknown[]) => apiFetch(...args),
  setAccessToken: (...args: unknown[]) => setAccessToken(...args),
}));

import { getCurrentUser, login } from "./session";

describe("session", () => {
  beforeEach(() => {
    apiFetch.mockReset();
    setAccessToken.mockReset();
  });

  it("getCurrentUser fetches GET /auth/me", async () => {
    const user = { id: "user-1", email: "dm@anahita.dev", username: "dm" };
    apiFetch.mockResolvedValueOnce(user);

    await expect(getCurrentUser()).resolves.toEqual(user);
    expect(apiFetch).toHaveBeenCalledWith("/auth/me");
  });

  it("login stores the access token and resolves the profile via /auth/me", async () => {
    const user = { id: "user-1", email: "dm@anahita.dev", username: "dm" };
    apiFetch
      .mockResolvedValueOnce({ access_token: "token-abc", token_type: "bearer" })
      .mockResolvedValueOnce(user);

    await expect(login("dm@anahita.dev", "correct-horse")).resolves.toEqual(user);

    expect(apiFetch).toHaveBeenNthCalledWith(1, "/auth/login", {
      method: "POST",
      body: JSON.stringify({ email: "dm@anahita.dev", password: "correct-horse" }),
      skipAuthRefresh: true,
    });
    expect(setAccessToken).toHaveBeenCalledWith("token-abc");
    expect(apiFetch).toHaveBeenNthCalledWith(2, "/auth/me");
  });
});
