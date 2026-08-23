import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import LandingPage from "./page";

describe("LandingPage", () => {
  it("renders the hero and CTAs without errors", () => {
    render(<LandingPage />);

    expect(
      screen.getByRole("heading", { name: /gerencie suas campanhas/i }),
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /entrar/i })).toHaveAttribute(
      "href",
      "/auth/login",
    );
    expect(screen.getByRole("link", { name: /criar conta/i })).toHaveAttribute(
      "href",
      "/auth/register",
    );
  });
});
