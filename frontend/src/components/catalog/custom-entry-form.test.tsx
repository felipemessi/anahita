import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const useCreateCustomEntry = vi.fn();
vi.mock("@/hooks/use-catalog", () => ({
  useCreateCustomEntry: (...args: unknown[]) => useCreateCustomEntry(...args),
}));

import { CustomEntryForm } from "./custom-entry-form";

describe("CustomEntryForm", () => {
  const mutateAsync = vi.fn();

  beforeEach(() => {
    mutateAsync.mockReset();
    mutateAsync.mockResolvedValue({ id: "monster-99" });
    useCreateCustomEntry.mockReset();
    useCreateCustomEntry.mockReturnValue({ mutateAsync, isPending: false });
  });

  it("never renders a campaign_id field — it is injected by the API layer, not the form", () => {
    render(<CustomEntryForm category="monsters" campaignId="camp-1" />);
    expect(screen.queryByLabelText(/campaign/i)).not.toBeInTheDocument();
    expect(useCreateCustomEntry).toHaveBeenCalledWith("monsters", "camp-1");
  });

  it("submits only the entered field values — is_custom/campaign_id are added by lib/api/catalog.ts", async () => {
    render(<CustomEntryForm category="monsters" campaignId="camp-1" />);

    fireEvent.change(screen.getByLabelText(/^nome$/i), {
      target: { value: "Homebrew Beast" },
    });
    fireEvent.change(screen.getByLabelText(/tamanho/i), {
      target: { value: "large" },
    });
    fireEvent.change(screen.getByLabelText(/tipo de criatura/i), {
      target: { value: "beast" },
    });
    fireEvent.change(screen.getByLabelText(/pontos de vida/i), {
      target: { value: "45" },
    });
    fireEvent.change(screen.getByLabelText(/desafio/i), {
      target: { value: "3" },
    });

    fireEvent.click(screen.getByRole("button", { name: /criar homebrew/i }));

    await screen.findByRole("button", { name: /criar homebrew/i });
    expect(mutateAsync).toHaveBeenCalledWith(
      expect.objectContaining({
        name: "Homebrew Beast",
        size: "large",
        creature_type: "beast",
        hit_points: 45,
        challenge_rating: 3,
      }),
    );
    const [payload] = mutateAsync.mock.calls[0] as [Record<string, unknown>];
    expect(payload).not.toHaveProperty("campaign_id");
    expect(payload).not.toHaveProperty("is_custom");
  });

  it("uses 'desc' (not 'description') for the rules category, matching RuleCreate", async () => {
    render(<CustomEntryForm category="rules" campaignId="camp-1" />);

    // Only one "Descrição" field for rules (the "desc"-keyed one) — the
    // common "description" field is omitted since RuleCreate has no such field.
    expect(screen.getAllByLabelText(/^descrição$/i)).toHaveLength(1);

    fireEvent.change(screen.getByLabelText(/^nome$/i), {
      target: { value: "House Rule: Flanking" },
    });
    fireEvent.change(screen.getByLabelText(/^descrição$/i), {
      target: { value: "Flanking grants advantage." },
    });
    fireEvent.click(screen.getByRole("button", { name: /criar homebrew/i }));

    await screen.findByRole("button", { name: /criar homebrew/i });
    expect(mutateAsync).toHaveBeenCalledWith(
      expect.objectContaining({
        name: "House Rule: Flanking",
        desc: "Flanking grants advantage.",
      }),
    );
    const [payload] = mutateAsync.mock.calls[0] as [Record<string, unknown>];
    expect(payload).not.toHaveProperty("description");
  });

  it("splits background fields (personality_traits/ideals/bonds/flaws), no description", () => {
    render(<CustomEntryForm category="backgrounds" campaignId="camp-1" />);
    expect(screen.queryByLabelText(/^descrição$/i)).not.toBeInTheDocument();
    expect(screen.getByLabelText(/traços de personalidade/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/ideais/i)).toBeInTheDocument();
  });
});
