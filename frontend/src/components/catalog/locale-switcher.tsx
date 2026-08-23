"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import {
  getClientLocale,
  setClientLocale,
  SUPPORTED_LOCALES,
  type Locale,
} from "@/lib/i18n/locale";

/**
 * Query key prefix shared with `hooks/use-catalog.ts` (Fase 1): every
 * catalog query must start its key with this tuple so switching locale can
 * invalidate all of them in one call.
 */
export const CATALOG_QUERY_KEY_PREFIX = ["catalog"] as const;

const LOCALE_LABELS: Record<Locale, string> = {
  en: "English",
  "pt-BR": "Português (BR)",
};

/**
 * Header control to switch the catalog (SRD) display locale. Persists the
 * choice as a cookie and invalidates any cached catalog queries so the next
 * render fetches content in the new locale.
 */
export function LocaleSwitcher() {
  const queryClient = useQueryClient();
  const [locale, setLocale] = useState<Locale>(() => getClientLocale());

  function handleChange(next: Locale) {
    if (next === locale) return;
    setClientLocale(next);
    setLocale(next);
    void queryClient.invalidateQueries({ queryKey: CATALOG_QUERY_KEY_PREFIX });
  }

  return (
    <label className="flex items-center gap-2 text-sm">
      <span className="sr-only">Idioma do catálogo</span>
      <select
        aria-label="Idioma do catálogo"
        value={locale}
        onChange={(e) => handleChange(e.target.value as Locale)}
        className="rounded-md border border-input bg-background px-2 py-1 text-sm"
      >
        {SUPPORTED_LOCALES.map((code) => (
          <option key={code} value={code}>
            {LOCALE_LABELS[code]}
          </option>
        ))}
      </select>
    </label>
  );
}
