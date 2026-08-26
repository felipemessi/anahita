import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const useUpdateCharacterCurrency = vi.fn();
vi.mock("@/hooks/use-character", () => ({
  useUpdateCharacterCurrency: () => useUpdateCharacterCurrency(),
}));

import { ApiError } from "@/lib/api/client";

import { CurrencyTracker } from "./currency-tracker";

describe("CurrencyTracker", () => {
  const mutateAsync = vi.fn();

  beforeEach(() => {
    mutateAsync.mockReset();
    mutateAsync.mockResolvedValue(undefined);
    useUpdateCharacterCurrency.mockReturnValue({ mutateAsync, isPending: false });
  });

  it("splits the copper balance into denominations for display (no ep)", () => {
    render(<CurrencyTracker characterId="char-1" currencyCp={1234} />);

    // 1234 cp -> 1 PP, 2 GP, 3 SP, 4 CP.
    expect(screen.getByText("1 PP 2 GP 3 SP 4 CP")).toBeInTheDocument();
  });

  it("a single-denomination gain computes the right copper delta", async () => {
    render(<CurrencyTracker characterId="char-1" currencyCp={0} />);

    fireEvent.change(screen.getByLabelText("GP"), { target: { value: "5" } });
    fireEvent.click(screen.getByRole("button", { name: "Registrar" }));

    await waitFor(() => expect(mutateAsync).toHaveBeenCalledWith({ delta: 500 }));
  });

  it("a mixed gain/spend across denominations computes the combined copper delta", async () => {
    render(<CurrencyTracker characterId="char-1" currencyCp={1000} />);

    // +2 gp -5 sp -> +200cp -50cp = +150cp
    fireEvent.change(screen.getByLabelText("GP"), { target: { value: "2" } });
    fireEvent.change(screen.getByLabelText("SP"), { target: { value: "-5" } });
    fireEvent.click(screen.getByRole("button", { name: "Registrar" }));

    await waitFor(() => expect(mutateAsync).toHaveBeenCalledWith({ delta: 150 }));
  });

  it("disables the submit button when every denomination is empty/zero", () => {
    render(<CurrencyTracker characterId="char-1" currencyCp={0} />);

    expect(screen.getByRole("button", { name: "Registrar" })).toBeDisabled();
  });

  it("shows the backend's insufficient-funds error", async () => {
    mutateAsync.mockRejectedValue(
      new ApiError(422, "Insufficient funds: balance is 10 cp, cannot spend 50 cp"),
    );
    render(<CurrencyTracker characterId="char-1" currencyCp={10} />);

    fireEvent.change(screen.getByLabelText("SP"), { target: { value: "-5" } });
    fireEvent.click(screen.getByRole("button", { name: "Registrar" }));

    expect(await screen.findByText(/insufficient funds/i)).toBeInTheDocument();
  });
});
