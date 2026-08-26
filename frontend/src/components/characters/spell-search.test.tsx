import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const useCatalogList = vi.fn();
vi.mock("@/hooks/use-catalog", () => ({
  useCatalogList: (...args: unknown[]) => useCatalogList(...args),
}));

import { SpellSearch } from "./spell-search";

const bless = {
  id: "spell-bless",
  index: "bless",
  name: "Bless",
  level: 1,
  school: "enchantment",
  ritual: false,
  concentration: true,
  is_custom: false,
  classes: [
    { id: "cleric-id", name: "Cleric" },
    { id: "druid-id", name: "Druid" },
  ],
};

const fireBolt = {
  id: "spell-fire-bolt",
  index: "fire-bolt",
  name: "Fire Bolt",
  level: 0,
  school: "evocation",
  ritual: false,
  concentration: false,
  is_custom: false,
  classes: [{ id: "wizard-id", name: "Wizard" }],
};

describe("SpellSearch", () => {
  beforeEach(() => {
    useCatalogList.mockReturnValue({ data: [bless, fireBolt], isLoading: false });
  });

  it("shows which classes can cast each result", () => {
    render(
      <SpellSearch
        campaignId="camp-1"
        classIndex="cleric"
        excludeSpellIds={new Set()}
        onSelect={vi.fn()}
      />,
    );

    expect(screen.getByText("Cleric/Druid")).toBeInTheDocument();
    expect(screen.getByText("Wizard")).toBeInTheDocument();
  });

  it("filters by the character's active class by default", () => {
    render(
      <SpellSearch
        campaignId="camp-1"
        classIndex="cleric"
        excludeSpellIds={new Set()}
        onSelect={vi.fn()}
      />,
    );

    expect(useCatalogList).toHaveBeenCalledWith(
      "spells",
      expect.objectContaining({ class_index: "cleric" }),
    );
  });

  it("checking 'mostrar magias de todas as classes' drops the class filter", () => {
    render(
      <SpellSearch
        campaignId="camp-1"
        classIndex="cleric"
        excludeSpellIds={new Set()}
        onSelect={vi.fn()}
      />,
    );

    fireEvent.click(
      screen.getByRole("checkbox", { name: "Mostrar magias de todas as classes" }),
    );

    expect(useCatalogList).toHaveBeenLastCalledWith(
      "spells",
      expect.not.objectContaining({ class_index: expect.anything() }),
    );
  });

  it("doesn't show the checkbox when there's no active class to filter by", () => {
    render(
      <SpellSearch
        campaignId="camp-1"
        classIndex={null}
        excludeSpellIds={new Set()}
        onSelect={vi.fn()}
      />,
    );

    expect(
      screen.queryByRole("checkbox", { name: "Mostrar magias de todas as classes" }),
    ).not.toBeInTheDocument();
  });

  it("selecting a spell calls onSelect with it", () => {
    const onSelect = vi.fn();
    render(
      <SpellSearch
        campaignId="camp-1"
        classIndex="cleric"
        excludeSpellIds={new Set()}
        onSelect={onSelect}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /bless/i }));

    expect(onSelect).toHaveBeenCalledWith(bless);
  });
});
