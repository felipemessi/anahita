"use client";

import { useEffect, useState } from "react";

import { useCharacter } from "@/hooks/use-character";
import { useCreateToken, useMap } from "@/hooks/use-map";
import { feetToCells } from "@/lib/utils/map-grid";
import { participantForToken, tokenForParticipant } from "@/lib/utils/map-token-match";
import { MapProvider } from "@/providers/map-provider";
import type { EncounterParticipant } from "@/types/combat";
import { MapCanvas } from "./map-canvas";

/**
 * Wires a `MapCanvas` to the live map WebSocket (`MapProvider`) and to the
 * current combat's turn/participants — movement range highlighting (Fase
 * 15 história 3) and map-driven target selection (história 5). Rendered by
 * the combat page only when its `Encounter.map_id` is set.
 *
 * Token selection state (which tokens are clicked) lives here, not in the
 * parent — `onSelectedParticipantsChange` is only called with the
 * *resolved* `EncounterParticipant` ids (via `participantForToken`), which
 * is what `ActionPicker` actually needs for `target_id`/
 * `additional_target_ids`; a token with no matching participant (not yet in
 * combat) is silently dropped from the selection.
 */
export function MapSection({
  mapId,
  isDm,
  encounterActive,
  currentTurnParticipant,
  participants,
  enableTargetSelection = false,
  onSelectedParticipantsChange,
}: {
  mapId: string;
  isDm: boolean;
  encounterActive: boolean;
  currentTurnParticipant: EncounterParticipant | undefined;
  participants: EncounterParticipant[];
  enableTargetSelection?: boolean;
  onSelectedParticipantsChange?: (participantIds: string[]) => void;
}) {
  return (
    <MapProvider mapId={mapId}>
      <MapSectionInner
        mapId={mapId}
        isDm={isDm}
        encounterActive={encounterActive}
        currentTurnParticipant={currentTurnParticipant}
        participants={participants}
        enableTargetSelection={enableTargetSelection}
        onSelectedParticipantsChange={onSelectedParticipantsChange}
      />
    </MapProvider>
  );
}

function MapSectionInner({
  mapId,
  isDm,
  encounterActive,
  currentTurnParticipant,
  participants,
  enableTargetSelection,
  onSelectedParticipantsChange,
}: {
  mapId: string;
  isDm: boolean;
  encounterActive: boolean;
  currentTurnParticipant: EncounterParticipant | undefined;
  participants: EncounterParticipant[];
  enableTargetSelection: boolean;
  onSelectedParticipantsChange?: (participantIds: string[]) => void;
}) {
  const { map, tokens, lastError, isConnected, moveToken } = useMap();
  const createToken = useCreateToken(mapId);
  const { data: currentTurnCharacter } = useCharacter(
    currentTurnParticipant?.character_id ?? "",
  );
  const [selectedTokenIds, setSelectedTokenIds] = useState<string[]>([]);

  useEffect(() => {
    if (!enableTargetSelection) setSelectedTokenIds([]);
  }, [enableTargetSelection]);

  useEffect(() => {
    if (!onSelectedParticipantsChange) return;
    const participantIds = selectedTokenIds
      .map((tokenId) => tokens.find((t) => t.id === tokenId))
      .filter((t): t is NonNullable<typeof t> => t !== undefined)
      .map((t) => participantForToken(t, participants)?.id)
      .filter((id): id is string => id !== undefined);
    onSelectedParticipantsChange(participantIds);
    // eslint-disable-next-line react-hooks/exhaustive-deps -- fires on selection change; tokens/participants are read, not depended on
  }, [selectedTokenIds]);

  if (!map) {
    return <p className="text-sm text-muted-foreground">Sincronizando mapa…</p>;
  }

  const currentTurnToken =
    encounterActive && currentTurnParticipant
      ? tokenForParticipant(currentTurnParticipant, tokens)
      : null;
  const movementRange =
    currentTurnToken && currentTurnCharacter
      ? {
          originX: currentTurnToken.x,
          originY: currentTurnToken.y,
          radiusCells: feetToCells(currentTurnCharacter.speed),
        }
      : null;

  function resolveTokenDisplay(token: (typeof tokens)[number]) {
    const linked = participantForToken(token, participants);
    return { name: linked?.name ?? token.name, portraitUrl: null };
  }

  function toggleTokenSelect(tokenId: string) {
    if (!enableTargetSelection) return;
    setSelectedTokenIds((ids) =>
      ids.includes(tokenId) ? ids.filter((id) => id !== tokenId) : [...ids, tokenId],
    );
  }

  const participantsWithoutToken = isDm
    ? participants.filter((p) => tokenForParticipant(p, tokens) === null)
    : [];

  function handleAddToken(p: EncounterParticipant) {
    createToken.mutate({
      character_id: p.character_id,
      npc_id: p.npc_id,
      monster_id: p.monster_id,
      name: p.name,
      x: 0,
      y: 0,
    });
  }

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between">
        <h2 className="font-semibold">{map.name}</h2>
        <span className={`text-xs ${isConnected ? "text-emerald-500" : "text-muted-foreground"}`}>
          {isConnected ? "Conectado" : "Conectando…"}
        </span>
      </div>
      {participantsWithoutToken.length > 0 ? (
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <span className="text-muted-foreground">Sem token no mapa:</span>
          {participantsWithoutToken.map((p) => (
            <button
              key={p.id}
              type="button"
              onClick={() => handleAddToken(p)}
              disabled={createToken.isPending}
              className="rounded-md border border-border px-2 py-1 hover:bg-secondary disabled:opacity-50"
            >
              + {p.name}
            </button>
          ))}
        </div>
      ) : null}
      {enableTargetSelection ? (
        <p className="text-xs text-muted-foreground">
          Clique em um ou mais tokens para selecionar o(s) alvo(s).
        </p>
      ) : null}
      {lastError ? (
        <p role="alert" className="text-sm text-destructive">
          {lastError}
        </p>
      ) : null}
      <MapCanvas
        map={map}
        tokens={tokens}
        isDm={isDm}
        onMoveToken={moveToken}
        movementRange={movementRange}
        resolveTokenDisplay={resolveTokenDisplay}
        selectedTokenIds={selectedTokenIds}
        onToggleTokenSelect={enableTargetSelection ? toggleTokenSelect : undefined}
      />
    </div>
  );
}
