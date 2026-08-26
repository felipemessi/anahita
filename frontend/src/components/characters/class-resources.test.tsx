import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const useSpendCharacterResource = vi.fn();
const useResourceOptions = vi.fn();
vi.mock("@/hooks/use-character", () => ({
  useSpendCharacterResource: () => useSpendCharacterResource(),
  useResourceOptions: (...args: unknown[]) => useResourceOptions(...args),
}));

import { ApiError } from "@/lib/api/client";

import { ClassResources } from "./class-resources";

describe("ClassResources", () => {
  const mutateAsync = vi.fn();

  beforeEach(() => {
    mutateAsync.mockReset();
    mutateAsync.mockResolvedValue(undefined);
    useSpendCharacterResource.mockReturnValue({ mutateAsync, isPending: false });
    useResourceOptions.mockReturnValue({ data: [] });
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

  it("using a resource with no options decrements it directly", async () => {
    render(
      <ClassResources
        characterId="char-1"
        resources={[{ resource_key: "ki_points", used: 0, max: 2 }]}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Usar" }));

    await waitFor(() =>
      expect(mutateAsync).toHaveBeenCalledWith({ resourceKey: "ki_points", optionId: undefined }),
    );
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

  it("a resource with multiple options requires a selection before 'usar' is enabled", async () => {
    useResourceOptions.mockReturnValue({
      data: [
        { id: "opt-1", feature_name: "Turn Undead" },
        { id: "opt-2", feature_name: "Preserve Life" },
      ],
    });
    render(
      <ClassResources
        characterId="char-1"
        resources={[{ resource_key: "channel_divinity_charges", used: 0, max: 1 }]}
      />,
    );

    const useButton = screen.getByRole("button", { name: "Usar" });
    expect(useButton).toBeDisabled();

    fireEvent.change(screen.getByLabelText("Opção de Canalizar divindade"), {
      target: { value: "opt-2" },
    });
    expect(useButton).not.toBeDisabled();

    fireEvent.click(useButton);
    await waitFor(() =>
      expect(mutateAsync).toHaveBeenCalledWith({
        resourceKey: "channel_divinity_charges",
        optionId: "opt-2",
      }),
    );
  });

  it("a resource with a single option uses directly, without a selector", () => {
    useResourceOptions.mockReturnValue({
      data: [{ id: "opt-1", feature_name: "Only Option" }],
    });
    render(
      <ClassResources
        characterId="char-1"
        resources={[{ resource_key: "channel_divinity_charges", used: 0, max: 1 }]}
      />,
    );

    expect(screen.queryByLabelText("Opção de Canalizar divindade")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Usar" })).not.toBeDisabled();
  });
});
