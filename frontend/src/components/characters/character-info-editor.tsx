"use client";

import { useState, type FormEvent } from "react";

import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { useUpdateCharacterInfo } from "@/hooks/use-character";
import { ApiError } from "@/lib/api/client";
import type { AbilityScore } from "@/types/catalog";
import type { Character, CharacterAbilityScoreCreate, CharacterUpdate } from "@/types/character";

const ABILITY_ORDER: AbilityScore[] = ["str", "dex", "con", "int", "wis", "cha"];

const ABILITY_LABELS: Record<AbilityScore, string> = {
  str: "Força",
  dex: "Destreza",
  con: "Constituição",
  int: "Inteligência",
  wis: "Sabedoria",
  cha: "Carisma",
};

/**
 * Inline editor for a character's name/alignment/background/ability-score
 * base values (PRD frontend backlog Fase 10) — same open/close + draft
 * pattern as the "PV atual" input in `CharacterSheet`, expanded into a
 * collapsible form since it covers several fields at once. Race/class are
 * not editable (backend keeps them locked).
 *
 * Editing an ability score requires an extra confirmation step: the change
 * cascades into AC (DEX) and max HP (CON) recalculated server-side, so the
 * player is warned before the request goes out. Name/alignment/background
 * edits send immediately, no confirmation needed.
 */
export function CharacterInfoEditor({ character }: { character: Character }) {
  const updateInfo = useUpdateCharacterInfo(character.id);
  const [open, setOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pendingUpdate, setPendingUpdate] = useState<CharacterUpdate | null>(null);

  const [name, setName] = useState(character.name);
  const [alignment, setAlignment] = useState(character.alignment ?? "");
  const [background, setBackground] = useState(character.background ?? "");
  const [abilityDrafts, setAbilityDrafts] = useState<Record<AbilityScore, string>>(() =>
    Object.fromEntries(
      character.ability_scores.map((score) => [score.ability, String(score.base_score)]),
    ) as Record<AbilityScore, string>,
  );

  function resetDrafts() {
    setName(character.name);
    setAlignment(character.alignment ?? "");
    setBackground(character.background ?? "");
    setAbilityDrafts(
      Object.fromEntries(
        character.ability_scores.map((score) => [score.ability, String(score.base_score)]),
      ) as Record<AbilityScore, string>,
    );
    setError(null);
  }

  function handleToggle() {
    if (open) {
      resetDrafts();
    }
    setOpen(!open);
  }

  function buildUpdate(): CharacterUpdate | null {
    const update: CharacterUpdate = {};

    if (name.trim() && name !== character.name) {
      update.name = name.trim();
    }
    const alignmentValue = alignment.trim() || null;
    if (alignmentValue !== (character.alignment ?? null)) {
      update.alignment = alignmentValue;
    }
    const backgroundValue = background.trim() || null;
    if (backgroundValue !== (character.background ?? null)) {
      update.background = backgroundValue;
    }

    const changedAbilities: CharacterAbilityScoreCreate[] = [];
    for (const score of character.ability_scores) {
      const draft = abilityDrafts[score.ability];
      const draftValue = Number(draft);
      if (draft !== undefined && draft !== "" && !Number.isNaN(draftValue) && draftValue !== score.base_score) {
        changedAbilities.push({ ability: score.ability, base_score: draftValue });
      }
    }
    if (changedAbilities.length > 0) {
      update.ability_scores = changedAbilities;
    }

    if (Object.keys(update).length === 0) return null;
    return update;
  }

  async function submitUpdate(update: CharacterUpdate) {
    setError(null);
    try {
      await updateInfo.mutateAsync(update);
      setOpen(false);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Não foi possível salvar as alterações.");
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const update = buildUpdate();
    if (!update) {
      setOpen(false);
      return;
    }
    if (update.ability_scores && update.ability_scores.length > 0) {
      setPendingUpdate(update);
      return;
    }
    await submitUpdate(update);
  }

  async function handleConfirmAbilityChange() {
    if (!pendingUpdate) return;
    const update = pendingUpdate;
    setPendingUpdate(null);
    await submitUpdate(update);
  }

  if (!open) {
    return (
      <button
        type="button"
        onClick={handleToggle}
        className="text-sm text-muted-foreground underline hover:text-foreground"
      >
        Editar informações
      </button>
    );
  }

  return (
    <section
      aria-label="Editar informações do personagem"
      className="rounded-lg border border-border bg-card p-4"
    >
      <form onSubmit={handleSubmit} className="space-y-3">
        <div className="grid gap-3 sm:grid-cols-3">
          <div className="space-y-1">
            <label htmlFor="char-name" className="text-xs text-muted-foreground">
              Nome
            </label>
            <input
              id="char-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full rounded-md border border-input bg-background px-2 py-1.5 text-sm"
            />
          </div>
          <div className="space-y-1">
            <label htmlFor="char-alignment" className="text-xs text-muted-foreground">
              Alinhamento
            </label>
            <input
              id="char-alignment"
              value={alignment}
              onChange={(e) => setAlignment(e.target.value)}
              placeholder="ex.: Leal e Bom"
              className="w-full rounded-md border border-input bg-background px-2 py-1.5 text-sm"
            />
          </div>
          <div className="space-y-1">
            <label htmlFor="char-background" className="text-xs text-muted-foreground">
              Antecedente
            </label>
            <input
              id="char-background"
              value={background}
              onChange={(e) => setBackground(e.target.value)}
              placeholder="ex.: Órfão"
              className="w-full rounded-md border border-input bg-background px-2 py-1.5 text-sm"
            />
          </div>
        </div>

        <div className="space-y-1">
          <p className="text-xs text-muted-foreground">Atributos-base</p>
          <div className="grid grid-cols-3 gap-2 sm:grid-cols-6">
            {ABILITY_ORDER.filter((ability) =>
              character.ability_scores.some((score) => score.ability === ability),
            ).map((ability) => (
              <div key={ability} className="space-y-1">
                <label htmlFor={`char-ability-${ability}`} className="text-xs text-muted-foreground">
                  {ABILITY_LABELS[ability]}
                </label>
                <input
                  id={`char-ability-${ability}`}
                  type="number"
                  value={abilityDrafts[ability] ?? ""}
                  onChange={(e) =>
                    setAbilityDrafts((prev) => ({ ...prev, [ability]: e.target.value }))
                  }
                  className="w-full rounded-md border border-input bg-background px-2 py-1.5 font-mono text-sm"
                />
              </div>
            ))}
          </div>
        </div>

        {error ? (
          <p role="alert" className="text-sm text-destructive">
            {error}
          </p>
        ) : null}

        <div className="flex items-center gap-2">
          <button
            type="submit"
            disabled={updateInfo.isPending}
            className="rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground hover:opacity-90 disabled:opacity-40"
          >
            Salvar
          </button>
          <button
            type="button"
            onClick={handleToggle}
            className="rounded-md border border-border px-3 py-1.5 text-sm hover:bg-secondary"
          >
            Cancelar
          </button>
        </div>
      </form>

      <ConfirmDialog
        open={pendingUpdate !== null}
        title="Alterar atributos-base"
        description="Alterar um atributo-base pode mudar CA, PV máximo e bônus de perícias associados. Deseja continuar?"
        confirmLabel="Confirmar"
        onConfirm={handleConfirmAbilityChange}
        onCancel={() => setPendingUpdate(null)}
      />
    </section>
  );
}
