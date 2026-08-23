import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";

import { CATALOG_QUERY_KEY_PREFIX, LocaleSwitcher } from "./locale-switcher";

describe("LocaleSwitcher", () => {
  beforeEach(() => {
    document.cookie = "anahita_locale=; path=/; max-age=0";
  });

  it("invalidates cached catalog queries when the locale changes", async () => {
    const queryClient = new QueryClient();
    queryClient.setQueryData([...CATALOG_QUERY_KEY_PREFIX, "races"], [
      { id: "elf", name: "Elf" },
    ]);
    const racesQuery = queryClient.getQueryState([
      ...CATALOG_QUERY_KEY_PREFIX,
      "races",
    ]);
    expect(racesQuery?.isInvalidated).toBe(false);

    render(
      <QueryClientProvider client={queryClient}>
        <LocaleSwitcher />
      </QueryClientProvider>,
    );

    fireEvent.change(screen.getByLabelText(/idioma do catálogo/i), {
      target: { value: "pt-BR" },
    });

    const updated = queryClient.getQueryState([
      ...CATALOG_QUERY_KEY_PREFIX,
      "races",
    ]);
    expect(updated?.isInvalidated).toBe(true);
    expect(document.cookie).toContain("anahita_locale=pt-BR");
  });

  it("does not invalidate when re-selecting the current locale", () => {
    const queryClient = new QueryClient();
    queryClient.setQueryData([...CATALOG_QUERY_KEY_PREFIX, "races"], []);

    render(
      <QueryClientProvider client={queryClient}>
        <LocaleSwitcher />
      </QueryClientProvider>,
    );

    fireEvent.change(screen.getByLabelText(/idioma do catálogo/i), {
      target: { value: "en" },
    });

    const state = queryClient.getQueryState([
      ...CATALOG_QUERY_KEY_PREFIX,
      "races",
    ]);
    expect(state?.isInvalidated).toBe(false);
  });
});
