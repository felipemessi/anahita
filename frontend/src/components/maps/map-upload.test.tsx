import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const useUploadMap = vi.fn();
vi.mock("@/hooks/use-map", () => ({
  useUploadMap: () => useUploadMap(),
}));

import { MapUpload } from "./map-upload";

class FakeImage {
  onload: (() => void) | null = null;
  naturalWidth = 1000;
  naturalHeight = 800;
  set src(_value: string) {
    // Simulate the image finishing "decode" synchronously.
    this.onload?.();
  }
}

describe("MapUpload", () => {
  beforeEach(() => {
    vi.stubGlobal("Image", FakeImage);
    vi.stubGlobal("URL", { ...URL, createObjectURL: vi.fn(() => "blob:fake") });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("reads the picked image's pixel size and submits it with the mutation", async () => {
    const mutateAsync = vi.fn().mockResolvedValue({});
    useUploadMap.mockReturnValue({ mutateAsync, isPending: false });

    render(<MapUpload sessionId="sess-1" />);

    const file = new File(["fake-png"], "tavern.png", { type: "image/png" });
    fireEvent.change(screen.getByLabelText("Imagem do mapa"), { target: { files: [file] } });

    await waitFor(() => expect(screen.getByText(/1000×800px/)).toBeInTheDocument());

    fireEvent.change(screen.getByLabelText("Nome"), { target: { value: "Old Tavern" } });
    fireEvent.click(screen.getByRole("button", { name: "Enviar mapa" }));

    await waitFor(() =>
      expect(mutateAsync).toHaveBeenCalledWith({
        fields: { name: "Old Tavern", width_px: 1000, height_px: 800, grid_size_px: 50 },
        file,
      }),
    );
  });

  it("submit is disabled until a file and a name are provided", () => {
    useUploadMap.mockReturnValue({ mutateAsync: vi.fn(), isPending: false });

    render(<MapUpload sessionId="sess-1" />);

    expect(screen.getByRole("button", { name: "Enviar mapa" })).toBeDisabled();
  });
});
