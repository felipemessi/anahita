import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const useSpendCharacterResource = vi.fn();
vi.mock("@/hooks/use-character", () => ({
  useSpendCharacterResource: () => useSpendCharacterResource(),
}));

import { ApiError } from "@/lib/api/client";

import { ClassResources } from "./class-resources";

describe("ClassResources", () => {
  const mutateAsync = vi.fn();

  beforeEach(() => {
    mutateAsync.mockReset();
    mutateAsync.mockResolvedValue(undefined);
    useSpendCharacterResource.mockReturnValue({ mutateAsync, isPending: false });
  });

  it("renders nothing when the character has no trackable resources", () => {
    const { container } = render(
      <ClassResources characterId="char-1" resources={[]} />,
    );

    expect(container).toBeEmptyDOMElement();
  });

  it("shows available/max for each resource", () => {
    render(
      <ClassResources
        characterId="char-1"
        resources={[{ resource_key: "rage_count", used: 1, max: 3 }]}
      />,
    );

    expect(screen.getByText("Fúria")).toBeInTheDocument();
    expect(screen.getByText("2/3")).toBeInTheDocument();
  });

  it("using a resource decrements it via the mutation", async () => {
    render(
      <ClassResources
        characterId="char-1"
        resources={[{ resource_key: "ki_points", used: 0, max: 2 }]}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Usar" }));

    await waitFor(() => expect(mutateAsync).toHaveBeenCalledWith("ki_points"));
  });

  it("disables the button once at the limit", () => {
    render(
      <ClassResources
        characterId="char-1"
        resources={[{ resource_key: "ki_points", used: 2, max: 2 }]}
      />,
    );

    expect(screen.getByRole("button", { name: "Usar" })).toBeDisabled();
  });

  it("shows the backend's error on failure", async () => {
    mutateAsync.mockRejectedValue(new ApiError(422, "No ki_points uses remaining (2/2 used)"));
    render(
      <ClassResources
        characterId="char-1"
        resources={[{ resource_key: "ki_points", used: 1, max: 2 }]}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Usar" }));

    expect(await screen.findByText(/no ki_points uses remaining/i)).toBeInTheDocument();
  });
});
