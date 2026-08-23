import { NextResponse, type NextRequest } from "next/server";

const REFRESH_COOKIE = "refresh_token";

/** Route prefixes reachable without an authenticated session. */
const PUBLIC_PATHS = ["/", "/auth", "/join"];

function isPublicPath(pathname: string): boolean {
  return PUBLIC_PATHS.some(
    (path) => pathname === path || pathname.startsWith(`${path}/`),
  );
}

/**
 * Route protection: redirects to /auth/login when there is no refresh-token
 * cookie and the requested path isn't public. See PRD §4.4.
 */
export function authMiddleware(request: NextRequest): NextResponse {
  const { pathname } = request.nextUrl;

  if (isPublicPath(pathname)) {
    return NextResponse.next();
  }

  const hasSession = Boolean(request.cookies.get(REFRESH_COOKIE)?.value);
  if (!hasSession) {
    const loginUrl = new URL("/auth/login", request.url);
    loginUrl.searchParams.set("next", pathname);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}
