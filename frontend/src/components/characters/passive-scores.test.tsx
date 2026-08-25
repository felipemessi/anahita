import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { PassiveScores } from "./passive-scores";

describe("PassiveScores", () => {
  it("renders the three values coming from the API", () => {
    render(
      <PassiveScores passivePerception={14} passiveInvestigation={11} passiveInsight={12} />,
    );

    expect(screen.getByText("Percepção passiva")).toBeInTheDocument();
    expect(screen.getByText("14")).toBeInTheDocument();
    expect(screen.getByText("Investigação passiva")).toBeInTheDocument();
    expect(screen.getByText("11")).toBeInTheDocument();
    expect(screen.getByText("Intuição passiva")).toBeInTheDocument();
    expect(screen.getByText("12")).toBeInTheDocument();
  });
});
