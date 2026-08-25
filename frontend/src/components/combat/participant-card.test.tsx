import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const useCharacter = vi.fn();
vi.mock("@/hooks/use-character", () => ({
  useCharacter: (...args: unknown[]) => useCharacter(...args),
}));

const useCatalogEntry = vi.fn();
vi.mock("@/hooks/use-catalog", () => ({
  useCatalogEntry: (...args: unknown[]) => useCatalogEntry(...args),
}));

import { RollLogProvider } from "@/components/characters/roll-log";

import { ParticipantCard } from "./participant-card";

const baseParticipant = {
  id: "p-1",
  encounter_id: "enc-1",
  character_id: "char-1",
  npc_id: null,
  monster_id: null,
  name: "Aria",
  initiative: 15,
  hit_point_max: 20,
  hit_point_current: 20,
  temporary_hit_points: 0,
  armor_class: 14,
  turn_order: 0,
  is_active: true,
  conditions: [],
  effects: [],
  concentration_dc: null,
  legendary_actions_used: 0,
  reactions_used: 0,
};

describe("ParticipantCard", () => {
  beforeEach(() => {
    useCharacter.mockReturnValue({ data: undefined });
    useCatalogEntry.mockReturnValue({ data: undefined });
  });

  it("shows the concentration save DC when set", () => {
    render(
      <RollLogProvider>
        <ParticipantCard
          participant={{ ...baseParticipant, concentration_dc: 12 }}
          isCurrentTurn={false}
        />
      </RollLogProvider>,
    );

    expect(screen.getByText("Teste de concentração: CD 12")).toBeInTheDocument();
  });

  it("shows no concentration callout when concentration_dc is null", () => {
    render(
      <RollLogProvider>
        <ParticipantCard participant={baseParticipant} isCurrentTurn={false} />
      </RollLogProvider>,
    );

    expect(screen.queryByText(/teste de concentração/i)).not.toBeInTheDocument();
  });

  it("rolls the CON save using the character's computed save_bonus", () => {
    useCharacter.mockReturnValue({
      data: { ability_scores: [{ ability: "con", save_bonus: 4 }] },
    });
    render(
      <RollLogProvider>
        <ParticipantCard
          participant={{ ...baseParticipant, concentration_dc: 12 }}
          isCurrentTurn={false}
        />
      </RollLogProvider>,
    );

    const rollButton = screen.getByRole("button", {
      name: "Rolar Resistência de Constituição (+4)",
    });
    fireEvent.click(rollButton);

    expect(screen.getByRole("region", { name: "Rolagens recentes" })).toHaveTextContent(
      "Resistência de Constituição",
    );
  });
});
