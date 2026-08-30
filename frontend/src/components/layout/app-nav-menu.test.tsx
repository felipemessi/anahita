import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

vi.mock("next/navigation", () => ({
  usePathname: () => "/campaigns/campaign-1/characters/char-1",
}));

import { AppNavMenu } from "./app-nav-menu";

describe("AppNavMenu", () => {
  it("is closed by default, so it never covers the page's own content", () => {
    render(<AppNavMenu campaignId="campaign-1" role="player" />);

    expect(screen.queryByRole("navigation", { name: "Navegação geral" })).not.toBeInTheDocument();
  });

  it("opens the general navigation on click", () => {
    render(<AppNavMenu campaignId="campaign-1" role="player" />);

    fireEvent.click(screen.getByRole("button", { name: /abrir navegação/i }));

    const nav = screen.getByRole("navigation", { name: "Navegação geral" });
    expect(nav).toBeInTheDocument();
    expect(screen.getByText("Personagens")).toBeInTheDocument();
    expect(screen.getByText("Catálogo")).toBeInTheDocument();
  });

  it("hides DM-only items for a player", () => {
    render(<AppNavMenu campaignId="campaign-1" role="player" />);
    fireEvent.click(screen.getByRole("button", { name: /abrir navegação/i }));

    expect(screen.queryByText("Diário")).not.toBeInTheDocument();
  });

  it("shows DM-only items for the DM", () => {
    render(<AppNavMenu campaignId="campaign-1" role="dm" />);
    fireEvent.click(screen.getByRole("button", { name: /abrir navegação/i }));

    expect(screen.getByText("Diário")).toBeInTheDocument();
  });

  it("closes again on a second click", () => {
    render(<AppNavMenu campaignId="campaign-1" role="player" />);
    const toggle = screen.getByRole("button", { name: /abrir navegação/i });

    fireEvent.click(toggle);
    expect(screen.getByRole("navigation", { name: "Navegação geral" })).toBeInTheDocument();

    fireEvent.click(toggle);
    expect(screen.queryByRole("navigation", { name: "Navegação geral" })).not.toBeInTheDocument();
  });

  it("closes when a nav item is clicked", () => {
    render(<AppNavMenu campaignId="campaign-1" role="player" />);
    fireEvent.click(screen.getByRole("button", { name: /abrir navegação/i }));

    fireEvent.click(screen.getByText("Catálogo"));

    expect(screen.queryByRole("navigation", { name: "Navegação geral" })).not.toBeInTheDocument();
  });
});
