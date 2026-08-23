import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { QueryProvider } from "./query-provider";
import { ThemeProvider } from "./theme-provider";

describe("app providers", () => {
  it("renders children without throwing (smoke test)", () => {
    render(
      <ThemeProvider>
        <QueryProvider>
          <p>ready</p>
        </QueryProvider>
      </ThemeProvider>,
    );

    expect(screen.getByText("ready")).toBeInTheDocument();
  });
});
