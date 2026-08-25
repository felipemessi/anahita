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

  it("splits the copper balance into denominations for display", () => {
    render(<CurrencyTracker characterId="char-1" currencyCp={1234} />);

    // 1234 cp -> 1 pp, 2 gp, 3 sp, 4 cp.
    expect(screen.getByText("1 pp 2 gp 3 sp 4 cp")).toBeInTheDocument();
  });

  it("gaining currency posts a positive delta", async () => {
    render(<CurrencyTracker characterId="char-1" currencyCp={0} />);

    fireEvent.change(screen.getByLabelText(/quantidade/i), { target: { value: "50" } });
    fireEvent.click(screen.getByRole("button", { name: "Ganhar" }));

    await waitFor(() => expect(mutateAsync).toHaveBeenCalledWith({ delta: 50 }));
  });

  it("spending currency posts a negative delta", async () => {
    render(<CurrencyTracker characterId="char-1" currencyCp={100} />);

    fireEvent.change(screen.getByLabelText(/quantidade/i), { target: { value: "50" } });
    fireEvent.click(screen.getByRole("button", { name: "Gastar" }));

    await waitFor(() => expect(mutateAsync).toHaveBeenCalledWith({ delta: -50 }));
  });

  it("shows the backend's insufficient-funds error", async () => {
    mutateAsync.mockRejectedValue(
      new ApiError(422, "Insufficient funds: balance is 10 cp, cannot spend 50 cp"),
    );
    render(<CurrencyTracker characterId="char-1" currencyCp={10} />);

    fireEvent.change(screen.getByLabelText(/quantidade/i), { target: { value: "50" } });
    fireEvent.click(screen.getByRole("button", { name: "Gastar" }));

    expect(await screen.findByText(/insufficient funds/i)).toBeInTheDocument();
  });
});
