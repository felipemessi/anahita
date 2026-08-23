import type { NextRequest } from "next/server";

import { authMiddleware } from "@/lib/auth/middleware";

export function middleware(request: NextRequest) {
  return authMiddleware(request);
}

export const config = {
  // Run on every path except static assets and Next.js internals.
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
