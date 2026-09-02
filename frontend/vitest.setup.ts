import "@testing-library/jest-dom/vitest";

// jsdom doesn't implement PointerEvent (only MouseEvent) — components using
// onPointerDown/Move/Up (e.g. components/maps/map-canvas.tsx's drag-and-drop,
// Fase 15) need clientX/clientY to actually reach the handler via
// `fireEvent.pointerDown(el, { clientX, clientY })` in tests. A MouseEvent
// subclass is enough: PointerEvent only adds pointer-specific fields
// (pointerId, pressure, ...) our handlers don't read.
if (typeof window !== "undefined" && !("PointerEvent" in window)) {
  class PointerEventPolyfill extends MouseEvent {
    constructor(type: string, params: MouseEventInit = {}) {
      super(type, params);
    }
  }
  // @ts-expect-error — a minimal stand-in, not a spec-complete PointerEvent.
  window.PointerEvent = PointerEventPolyfill;
}

// jsdom does not implement matchMedia; next-themes reads it on mount.
if (typeof window !== "undefined" && !window.matchMedia) {
  window.matchMedia = (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  }) as unknown as MediaQueryList;
}
