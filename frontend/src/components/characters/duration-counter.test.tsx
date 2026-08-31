import { act, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { DurationCounter } from "./duration-counter";

describe("DurationCounter", () => {
  afterEach(() => {
    vi.useRealTimers();
  });

  it("renders nothing when not concentrating", () => {
    const { container } = render(
      <DurationCounter
        remaining={{ mode: null, remaining_rounds: null, remaining_seconds: null, expired: false }}
      />,
    );

    expect(container).toBeEmptyDOMElement();
  });

  it("shows an indefinite label for an indefinite duration", () => {
    render(
      <DurationCounter
        remaining={{ mode: "indefinite", remaining_rounds: null, remaining_seconds: null, expired: false }}
      />,
    );

    expect(screen.getByText("Duração indeterminada")).toBeInTheDocument();
  });

  describe("rounds mode", () => {
    it("shows the initial rounds remaining", () => {
      render(
        <DurationCounter
          remaining={{ mode: "rounds", remaining_rounds: 5, remaining_seconds: null, expired: false }}
          currentRound={3}
        />,
      );

      expect(screen.getByText("5 rodadas restantes")).toBeInTheDocument();
    });

    it("decrements by one each time currentRound advances a full round (turn_advanced)", () => {
      const { rerender } = render(
        <DurationCounter
          remaining={{ mode: "rounds", remaining_rounds: 3, remaining_seconds: null, expired: false }}
          currentRound={1}
        />,
      );
      expect(screen.getByText("3 rodadas restantes")).toBeInTheDocument();

      rerender(
        <DurationCounter
          remaining={{ mode: "rounds", remaining_rounds: 3, remaining_seconds: null, expired: false }}
          currentRound={2}
        />,
      );
      expect(screen.getByText("2 rodadas restantes")).toBeInTheDocument();

      rerender(
        <DurationCounter
          remaining={{ mode: "rounds", remaining_rounds: 3, remaining_seconds: null, expired: false }}
          currentRound={3}
        />,
      );
      expect(screen.getByText("1 rodada restante")).toBeInTheDocument();

      rerender(
        <DurationCounter
          remaining={{ mode: "rounds", remaining_rounds: 3, remaining_seconds: null, expired: false }}
          currentRound={4}
        />,
      );
      expect(screen.getByText("Duração expirada")).toBeInTheDocument();
    });

    it("highlights urgently in the last round before expiring", () => {
      render(
        <DurationCounter
          remaining={{ mode: "rounds", remaining_rounds: 1, remaining_seconds: null, expired: false }}
          currentRound={1}
        />,
      );

      expect(screen.getByRole("alert")).toHaveTextContent("1 rodada restante");
    });

    it("resets its baseline when a fresh remainingRounds value arrives", () => {
      const { rerender } = render(
        <DurationCounter
          remaining={{ mode: "rounds", remaining_rounds: 3, remaining_seconds: null, expired: false }}
          currentRound={1}
        />,
      );

      rerender(
        <DurationCounter
          remaining={{ mode: "rounds", remaining_rounds: 2, remaining_seconds: null, expired: false }}
          currentRound={1}
        />,
      );

      expect(screen.getByText("2 rodadas restantes")).toBeInTheDocument();
    });
  });

  describe("seconds mode", () => {
    beforeEach(() => {
      vi.useFakeTimers();
    });

    it("shows the initial seconds remaining, formatted mm:ss", () => {
      render(
        <DurationCounter
          remaining={{ mode: "seconds", remaining_rounds: null, remaining_seconds: 65, expired: false }}
        />,
      );

      expect(screen.getByText("1:05 restantes")).toBeInTheDocument();
    });

    it("expires at the right moment", () => {
      render(
        <DurationCounter
          remaining={{ mode: "seconds", remaining_rounds: null, remaining_seconds: 10, expired: false }}
        />,
      );

      expect(screen.getByText("0:10 restantes")).toBeInTheDocument();

      act(() => {
        vi.advanceTimersByTime(9000);
      });
      expect(screen.queryByText("Duração expirada")).not.toBeInTheDocument();

      act(() => {
        vi.advanceTimersByTime(1000);
      });
      expect(screen.getByText("Duração expirada")).toBeInTheDocument();
    });

    it("highlights urgently in the last seconds before expiring", () => {
      render(
        <DurationCounter
          remaining={{ mode: "seconds", remaining_rounds: null, remaining_seconds: 6, expired: false }}
        />,
      );

      expect(screen.getByRole("alert")).toHaveTextContent("0:06 restantes");
    });
  });
});
