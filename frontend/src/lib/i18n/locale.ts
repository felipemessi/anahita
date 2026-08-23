/**
 * Locale for catalog (SRD) content display — never the app UI itself.
 * See docs/anahita-frontend-prd.md §3.4.
 */

export const LOCALE_COOKIE = "anahita_locale";
export const DEFAULT_LOCALE = "en";
export const SUPPORTED_LOCALES = ["en", "pt-BR"] as const;

export type Locale = (typeof SUPPORTED_LOCALES)[number];

export function isSupportedLocale(value: string | undefined | null): value is Locale {
  return (SUPPORTED_LOCALES as readonly string[]).includes(value ?? "");
}

/** Client-side: read the current locale from `document.cookie` (falls back to default). */
export function getClientLocale(): Locale {
  if (typeof document === "undefined") return DEFAULT_LOCALE;
  const match = document.cookie.match(
    new RegExp(`(?:^|; )${LOCALE_COOKIE}=([^;]*)`),
  );
  const value = match?.[1] ? decodeURIComponent(match[1]) : undefined;
  return isSupportedLocale(value) ? value : DEFAULT_LOCALE;
}

/** Client-side: persist the chosen locale as a cookie readable by the server too. */
export function setClientLocale(locale: Locale): void {
  if (typeof document === "undefined") return;
  const oneYear = 60 * 60 * 24 * 365;
  document.cookie = `${LOCALE_COOKIE}=${locale}; path=/; max-age=${oneYear}; samesite=lax`;
}
