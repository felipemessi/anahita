import { beforeEach, describe, expect, it } from "vitest";

import { DEFAULT_LOCALE, getClientLocale, setClientLocale } from "./locale";

describe("locale cookie helpers", () => {
  beforeEach(() => {
    document.cookie = "anahita_locale=; path=/; max-age=0";
  });

  it("defaults to en when no cookie is set", () => {
    expect(getClientLocale()).toBe(DEFAULT_LOCALE);
  });

  it("persists and reads back a supported locale", () => {
    setClientLocale("pt-BR");
    expect(getClientLocale()).toBe("pt-BR");
  });

  it("falls back to default for an unsupported cookie value", () => {
    document.cookie = "anahita_locale=fr; path=/";
    expect(getClientLocale()).toBe(DEFAULT_LOCALE);
  });
});
