import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { CatalogList } from "./catalog-list";

describe("CatalogList", () => {
  it("shows an SRD badge for built-in entries and a Homebrew badge for custom ones", () => {
    render(
      <CatalogList
        campaignId="camp-1"
        category="races"
        entries={[
          { id: "race-1", name: "Elf", is_custom: false },
          { id: "race-2", name: "Custom Elf", is_custom: true },
        ]}
      />,
    );

    const elfLink = screen.getByRole("link", { name: /^elf srd$/i });
    expect(elfLink).toHaveTextContent("SRD");

    const customLink = screen.getByRole("link", { name: /custom elf homebrew/i });
    expect(customLink).toHaveTextContent("Homebrew");
  });

  it("shows an empty state when there are no entries", () => {
    render(<CatalogList campaignId="camp-1" category="races" entries={[]} />);
    expect(screen.getByText(/nenhum resultado/i)).toBeInTheDocument();
  });
});
