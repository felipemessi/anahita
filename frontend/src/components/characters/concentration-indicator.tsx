"use client";

import { useState } from "react";

import { DurationCounter } from "@/components/characters/duration-counter";
import { useCatalogEntry } from "@/hooks/use-catalog";
import { useSetCharacterConcentration } from "@/hooks/use-character";
import { ApiError } from "@/lib/api/client";
import { useOptionalCombatContext } from "@/providers/combat-provider";
import type { ConcentrationRemaining } from "@/types/character";

/**
 * "Concentrando em [magia]" indicator, with a button to end it early —
 * starting concentration happens automatically when casting a
 * concentration spell (`SpellListByCircle`'s "conjurar", via
 * `CharacterService.cast_spell`), which also drops whatever was already
 * being concentrated on, so there's no separate "iniciar" control here.
 * `concentrationRemaining` (Fase 12) drives the duration countdown below the
 * spell name — omitted, it renders no countdown (existing callers/tests
 * unaffected).
 */
export function ConcentrationIndicator({
  characterId,
  concentratingSpellId,
  concentrationRemaining,
}: {
  characterId: string;
  concentratingSpellId: string | null;
  concentrationRemaining?: ConcentrationRemaining | null;
}) {
  const setConcentration = useSetCharacterConcentration(characterId);
  const { data: spell } = useCatalogEntry("spells", concentratingSpellId ?? "");
  const [error, setError] = useState<string | null>(null);
  // `null` outside a CombatProvider (e.g. the standalone character sheet) —
  // rounds-mode countdown then just holds at its last fetched value.
  const combat = useOptionalCombatContext();
  const currentRound = combat?.encounter?.current_round ?? null;

  if (!concentratingSpellId) return null;

  async function handleEnd() {
    setError(null);
    try {
      await setConcentration.mutateAsync({ spell_id: null });
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Não foi possível encerrar a concentração.",
      );
    }
  }

  return (
    <section
      aria-label="Concentração"
      className="rounded-lg border border-border bg-card p-3 text-sm"
    >
      <p>
        Concentrando em{" "}
        <span className="font-medium">{spell?.name ?? "…"}</span>
      </p>
      {concentrationRemaining ? (
        <DurationCounter remaining={concentrationRemaining} currentRound={currentRound} />
      ) : null}
      <button
        type="button"
        onClick={handleEnd}
        disabled={setConcentration.isPending}
        className="mt-1 text-xs text-muted-foreground underline hover:text-foreground disabled:opacity-40"
      >
        Encerrar concentração
      </button>
      {error ? (
        <p role="alert" className="mt-1 text-xs text-destructive">
          {error}
        </p>
      ) : null}
    </section>
  );
}
