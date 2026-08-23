import { NextRequest } from "next/server";
import { describe, expect, it } from "vitest";

import { authMiddleware } from "./middleware";

function makeRequest(pathname: string, cookie?: string): NextRequest {
  const headers = new Headers();
  if (cookie) headers.set("cookie", cookie);
  return new NextRequest(new URL(pathname, "http://localhost:3000"), {
    headers,
  });
}

describe("authMiddleware", () => {
  it("redirects to /auth/login when a protected route has no session cookie", () => {
    const res = authMiddleware(makeRequest("/campaigns"));

    expect(res.status).toBe(307);
    expect(res.headers.get("location")).toContain("/auth/login");
  });

  it("allows a protected route through when the refresh_token cookie is present", () => {
    const res = authMiddleware(makeRequest("/campaigns", "refresh_token=abc123"));

    expect(res.status).toBe(200);
    expect(res.headers.get("location")).toBeNull();
  });

  it("allows public routes through without a session", () => {
    for (const path of ["/", "/auth/login", "/auth/register", "/join/xyz"]) {
      const res = authMiddleware(makeRequest(path));
      expect(res.headers.get("location")).toBeNull();
    }
  });
});
