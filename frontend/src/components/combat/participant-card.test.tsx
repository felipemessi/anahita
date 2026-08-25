import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

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
  it("shows the concentration save DC when set", () => {
    render(
      <ParticipantCard
        participant={{ ...baseParticipant, concentration_dc: 12 }}
        isCurrentTurn={false}
      />,
    );

    expect(screen.getByText("Teste de concentração: CD 12")).toBeInTheDocument();
  });

  it("shows no concentration callout when concentration_dc is null", () => {
    render(<ParticipantCard participant={baseParticipant} isCurrentTurn={false} />);

    expect(screen.queryByText(/teste de concentração/i)).not.toBeInTheDocument();
  });
});
