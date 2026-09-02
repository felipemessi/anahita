import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { MapCanvas } from "./map-canvas";
import type { MapToken, SessionMap } from "@/types/map";

const map: SessionMap = {
  id: "map-1",
  session_id: "sess-1",
  name: "Old Tavern",
  url: "/files/maps/map-1.png",
  width_px: 1000,
  height_px: 1000,
  grid_size_px: 50,
  created_at: "2026-01-01T00:00:00Z",
};

const token: MapToken = {
  id: "token-1",
  map_id: "map-1",
  character_id: "char-1",
  npc_id: null,
  monster_id: null,
  name: "Aria",
  x: 0,
  y: 0,
  is_visible: true,
};

function mockViewportRect() {
  vi.spyOn(HTMLElement.prototype, "getBoundingClientRect").mockReturnValue({
    left: 0,
    top: 0,
    right: 500,
    bottom: 500,
    width: 500,
    height: 500,
    x: 0,
    y: 0,
    toJSON: () => ({}),
  });
}

describe("MapCanvas", () => {
  it("dragging a movable token calls onMoveToken with the snapped destination cell", () => {
    mockViewportRect();
    const onMoveToken = vi.fn();

    render(
      <MapCanvas
        map={map}
        tokens={[token]}
        onMoveToken={onMoveToken}
        canMoveToken={() => true}
      />,
    );

    const tokenEl = screen.getByRole("button", { name: "Token: Aria" });
    fireEvent.pointerDown(tokenEl, { clientX: 25, clientY: 25 });
    fireEvent.pointerMove(tokenEl, { clientX: 175, clientY: 75 });
    fireEvent.pointerUp(tokenEl, { clientX: 175, clientY: 75 });

    // Moved to pixel (175, 75) -> cell (3, 1) at grid_size_px=50.
    expect(onMoveToken).toHaveBeenCalledWith("token-1", 3, 1);
  });

  it("a small pointer movement (click) toggles selection instead of moving", () => {
    mockViewportRect();
    const onMoveToken = vi.fn();
    const onToggleTokenSelect = vi.fn();

    render(
      <MapCanvas
        map={map}
        tokens={[token]}
        onMoveToken={onMoveToken}
        canMoveToken={() => true}
        onToggleTokenSelect={onToggleTokenSelect}
      />,
    );

    const tokenEl = screen.getByRole("button", { name: "Token: Aria" });
    fireEvent.pointerDown(tokenEl, { clientX: 25, clientY: 25 });
    fireEvent.pointerUp(tokenEl, { clientX: 26, clientY: 25 });

    expect(onToggleTokenSelect).toHaveBeenCalledWith("token-1");
    expect(onMoveToken).not.toHaveBeenCalled();
  });

  it("a token the viewer can't move doesn't call onMoveToken even after a drag", () => {
    mockViewportRect();
    const onMoveToken = vi.fn();

    render(
      <MapCanvas
        map={map}
        tokens={[token]}
        onMoveToken={onMoveToken}
        canMoveToken={() => false}
      />,
    );

    const tokenEl = screen.getByRole("button", { name: "Token: Aria" });
    fireEvent.pointerDown(tokenEl, { clientX: 25, clientY: 25 });
    fireEvent.pointerMove(tokenEl, { clientX: 175, clientY: 75 });
    fireEvent.pointerUp(tokenEl, { clientX: 175, clientY: 75 });

    expect(onMoveToken).not.toHaveBeenCalled();
  });

  it("clamps a drop beyond the map's edge to the last valid cell", () => {
    mockViewportRect();
    const onMoveToken = vi.fn();

    render(
      <MapCanvas
        map={map}
        tokens={[token]}
        onMoveToken={onMoveToken}
        canMoveToken={() => true}
      />,
    );

    const tokenEl = screen.getByRole("button", { name: "Token: Aria" });
    fireEvent.pointerDown(tokenEl, { clientX: 25, clientY: 25 });
    fireEvent.pointerMove(tokenEl, { clientX: 5000, clientY: 5000 });
    fireEvent.pointerUp(tokenEl, { clientX: 5000, clientY: 5000 });

    // map is 1000x1000 at 50px/cell -> last valid cell is (19, 19).
    expect(onMoveToken).toHaveBeenCalledWith("token-1", 19, 19);
  });

  it("renders movement range cells around the given origin", () => {
    mockViewportRect();

    render(
      <MapCanvas
        map={map}
        tokens={[token]}
        movementRange={{ originX: 5, originY: 5, radiusCells: 1 }}
      />,
    );

    expect(screen.getAllByTestId("movement-range-cell")).toHaveLength(9);
  });

  it("hides a token invisible to the viewer", () => {
    mockViewportRect();
    const hidden: MapToken = { ...token, id: "token-2", is_visible: false };

    render(<MapCanvas map={map} tokens={[hidden]} canMoveToken={() => false} />);

    expect(screen.queryByRole("button", { name: /Token:/ })).not.toBeInTheDocument();
  });
});
