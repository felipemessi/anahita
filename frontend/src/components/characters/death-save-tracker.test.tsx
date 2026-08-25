import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const useRollDeathSave = vi.fn();
vi.mock("@/hooks/use-character", () => ({
  useRollDeathSave: () => useRollDeathSave(),
}));

import { ApiError } from "@/lib/api/client";

import { DeathSaveTracker } from "./death-save-tracker";

describe("DeathSaveTracker", () => {
  const mutateAsync = vi.fn();

  beforeEach(() => {
    mutateAsync.mockReset();
    mutateAsync.mockResolvedValue(undefined);
    useRollDeathSave.mockReturnValue({ mutateAsync, isPending: false });
  });

  it("doesn't render when hit_point_current is above 0", () => {
    const { container } = render(
      <DeathSaveTracker
        characterId="char-1"
        hitPointCurrent={5}
        successes={0}
        failures={0}
        isDead={false}
      />,
    );

    expect(container).toBeEmptyDOMElement();
  });

  it("shows accumulated successes and failures at 0 HP", () => {
    render(
      <DeathSaveTracker
        characterId="char-1"
        hitPointCurrent={0}
        successes={2}
        failures={1}
        isDead={false}
      />,
    );

    expect(screen.getByLabelText("2 de 3 sucessos")).toBeInTheDocument();
    expect(screen.getByLabelText("1 de 3 falhas")).toBeInTheDocument();
  });

  it("rolling calls the death save endpoint", async () => {
    render(
      <DeathSaveTracker
        characterId="char-1"
        hitPointCurrent={0}
        successes={0}
        failures={0}
        isDead={false}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Rolar" }));

    await waitFor(() => expect(mutateAsync).toHaveBeenCalledWith({}));
  });

  it("shows a stabilized state after successes reset to 0/0 without dying", () => {
    const { rerender } = render(
      <DeathSaveTracker
        characterId="char-1"
        hitPointCurrent={0}
        successes={2}
        failures={0}
        isDead={false}
      />,
    );
    expect(screen.getByRole("button", { name: "Rolar" })).toBeInTheDocument();

    rerender(
      <DeathSaveTracker
        characterId="char-1"
        hitPointCurrent={0}
        successes={0}
        failures={0}
        isDead={false}
      />,
    );

    expect(screen.getByText("Estável")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Rolar" })).not.toBeInTheDocument();
  });

  it("shows a dead state with 3 failures and hides the roll button", () => {
    render(
      <DeathSaveTracker
        characterId="char-1"
        hitPointCurrent={0}
        successes={0}
        failures={3}
        isDead={true}
      />,
    );

    expect(screen.getByText("Morto")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Rolar" })).not.toBeInTheDocument();
  });

  it("shows the backend's error on failure", async () => {
    mutateAsync.mockRejectedValue(new ApiError(422, "Death saves only apply at 0 hit points"));
    render(
      <DeathSaveTracker
        characterId="char-1"
        hitPointCurrent={0}
        successes={0}
        failures={0}
        isDead={false}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Rolar" }));

    expect(await screen.findByText(/death saves only apply/i)).toBeInTheDocument();
  });
});
