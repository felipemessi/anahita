"use client";

import { useState } from "react";

import { useCatalogEntry } from "@/hooks/use-catalog";
import { useCombat } from "@/hooks/use-combat";
import { useNpcs } from "@/hooks/use-world";
import type { EncounterParticipant } from "@/types/combat";

/**
 * Every SRD monster with legendary actions gets this flat per-round budget
 * — mirrors `CombatService._LEGENDARY_ACTIONS_PER_ROUND` (the catalog
 * doesn't carry a per-monster override).
 */
const LEGENDARY_ACTIONS_PER_ROUND = 3;

/**
 * For a monster/NPC participant with a stat block, lists its available
 * legendary actions/reactions (via `monster-stat-block.tsx`'s data) with a
 * target selector and a per-round usage counter — disabled once the
 * round's budget is spent. Renders nothing for a PC or a stat-block-less
 * participant.
 */
export function LegendaryActionPicker({
  campaignId,
  participant,
  otherParticipants,
}: {
  campaignId: string;
  participant: EncounterParticipant;
  otherParticipants: EncounterParticipant[];
}) {
  const { data: npcs } = useNpcs(campaignId);
  const npcStatBlockId = participant.npc_id
    ? (npcs?.find((n) => n.id === participant.npc_id)?.stat_block_id ?? null)
    : null;
  const monsterId = participant.monster_id ?? npcStatBlockId;
  const { data: monster } = useCatalogEntry("monsters", monsterId ?? "");
  const { sendLegendaryAction, triggerReaction } = useCombat();

  const [legendaryActionId, setLegendaryActionId] = useState("");
  const [reactionId, setReactionId] = useState("");
  const [targetId, setTargetId] = useState(otherParticipants[0]?.id ?? "");

  if (!monster || (monster.legendary_actions.length === 0 && monster.reactions.length === 0)) {
    return null;
  }
  if (otherParticipants.length === 0) return null;

  const legendaryActionsLeft =
    LEGENDARY_ACTIONS_PER_ROUND - participant.legendary_actions_used;
  const reactionsLeft = 1 - participant.reactions_used;

  return (
    <div className="space-y-2 rounded-md border border-border p-2 text-xs">
      <label htmlFor={`legendary-target-${participant.id}`} className="sr-only">
        Alvo
      </label>
      <select
        id={`legendary-target-${participant.id}`}
        aria-label="Alvo"
        value={targetId}
        onChange={(e) => setTargetId(e.target.value)}
        className="w-full rounded-md border border-input bg-background px-2 py-1"
      >
        {otherParticipants.map((p) => (
          <option key={p.id} value={p.id}>
            {p.name}
          </option>
        ))}
      </select>

      {monster.legendary_actions.length > 0 ? (
        <div className="flex items-center gap-1">
          <select
            aria-label="Ação lendária"
            value={legendaryActionId}
            onChange={(e) => setLegendaryActionId(e.target.value)}
            className="flex-1 rounded-md border border-input bg-background px-2 py-1"
          >
            <option value="">Ação lendária…</option>
            {monster.legendary_actions.map((action) => (
              <option key={action.id} value={action.id}>
                {action.name}
              </option>
            ))}
          </select>
          <button
            type="button"
            onClick={() => sendLegendaryAction(participant.id, targetId, legendaryActionId)}
            disabled={!legendaryActionId || legendaryActionsLeft <= 0}
            className="rounded border border-border px-2 py-1 hover:bg-secondary disabled:opacity-40"
          >
            Usar ({legendaryActionsLeft}/{LEGENDARY_ACTIONS_PER_ROUND})
          </button>
        </div>
      ) : null}

      {monster.reactions.length > 0 ? (
        <div className="flex items-center gap-1">
          <select
            aria-label="Reação"
            value={reactionId}
            onChange={(e) => setReactionId(e.target.value)}
            className="flex-1 rounded-md border border-input bg-background px-2 py-1"
          >
            <option value="">Reação…</option>
            {monster.reactions.map((reaction) => (
              <option key={reaction.id} value={reaction.id}>
                {reaction.name}
              </option>
            ))}
          </select>
          <button
            type="button"
            onClick={() => triggerReaction(participant.id, targetId, reactionId)}
            disabled={!reactionId || reactionsLeft <= 0}
            className="rounded border border-border px-2 py-1 hover:bg-secondary disabled:opacity-40"
          >
            Disparar ({reactionsLeft}/1)
          </button>
        </div>
      ) : null}
    </div>
  );
}
