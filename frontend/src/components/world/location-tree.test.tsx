import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { LocationTree } from "./location-tree";

describe("LocationTree", () => {
  it("renders a region → city → tavern hierarchy nested correctly", () => {
    render(
      <LocationTree
        campaignId="campaign-1"
        tree={[
          {
            id: "region-1",
            name: "Sword Coast",
            location_type: "region",
            children: [
              {
                id: "city-1",
                name: "Waterdeep",
                location_type: "city",
                children: [
                  {
                    id: "tavern-1",
                    name: "Yawning Portal",
                    location_type: "building",
                    children: [],
                  },
                ],
              },
            ],
          },
        ]}
      />,
    );

    const region = screen.getByText(/Sword Coast/);
    const city = screen.getByText(/Waterdeep/);
    const tavern = screen.getByText(/Yawning Portal/);

    expect(region).toBeInTheDocument();
    // The tavern is nested inside the city's subtree, which is nested inside
    // the region's — not siblings at the top level.
    const regionItem = region.closest("li");
    expect(regionItem).not.toBeNull();
    expect(regionItem?.contains(city)).toBe(true);
    expect(regionItem?.contains(tavern)).toBe(true);

    const cityItem = city.closest("li");
    expect(cityItem?.contains(tavern)).toBe(true);
  });

  it("shows a placeholder when the campaign has no locations", () => {
    render(<LocationTree tree={[]} campaignId="campaign-1" />);
    expect(screen.getByText(/nenhum local/i)).toBeInTheDocument();
  });
});
