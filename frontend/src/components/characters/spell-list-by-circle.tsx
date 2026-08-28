"use client";

import { useState } from "react";

import { ABILITY_LABELS } from "@/components/characters/creation-wizard/wizard-state";
import { useRoll, useRollDamage } from "@/components/characters/roll-log";
import { circleLabel, SpellSearch } from "@/components/characters/spell-search";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { useCatalogEntry, useCatalogList } from "@/hooks/use-catalog";
import {
  useAddCharacterSpell,
  useCastCharacterSpell,
  useRemoveCharacterSpell,
  useSpellAttackProfile,
  useUpdateCharacterSpell,
} from "@/hooks/use-character";
import { ApiError } from "@/lib/api/client";
import type { ClassSummary, SpellSummary } from "@/types/catalog";
import type { CharacterClass, CharacterSpell, CharacterSpellSlot } from "@/types/character";

/**
 * Known spells grouped by circle (0 = truques), with prepare/unprepare,
 * remove, an expandable detail, and a search to add another — replaces the
 * old flat list + single-select `spell-slots.tsx` used to be (that file now
 * shows numeric slot counters instead, see `spell-slots.tsx`).
 */
export function SpellListByCircle({
  characterId,
  campaignId,
  spells,
  classes,
  spellSlots,
}: {
  characterId: string;
  campaignId: string;
  spells: CharacterSpell[];
  classes: CharacterClass[];
  spellSlots: CharacterSpellSlot[];
}) {
  const { data: catalogClasses } = useCatalogList("classes", {
    campaign_id: campaignId,
  });
  const { data: catalogSpells } = useCatalogList("spells", { campaign_id: campaignId });
  const addSpell = useAddCharacterSpell(characterId);
  const updateSpell = useUpdateCharacterSpell(characterId);
  const removeSpell = useRemoveCharacterSpell(characterId);
  const castSpell = useCastCharacterSpell(characterId);
  const [error, setError] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [castLevelBySpell, setCastLevelBySpell] = useState<Record<string, number>>({});
  const [togglingId, setTogglingId] = useState<string | null>(null);

  const classOptions = classes
    .map((c) => catalogClasses?.find((cc) => cc.id === c.class_definition_id))
    .filter((c): c is ClassSummary => Boolean(c));
  const [sourceClassIndex, setSourceClassIndex] = useState<string | null>(null);
  const activeClassIndex = sourceClassIndex ?? classOptions[0]?.index ?? null;
  const activeClassOption = classOptions.find((c) => c.index === activeClassIndex);
  const { data: activeClassDetail } = useCatalogEntry("classes", activeClassOption?.id ?? "");
  const [pendingAddSpell, setPendingAddSpell] = useState<SpellSummary | null>(null);

  function nameFor(spellId: string): string {
    return catalogSpells?.find((s) => s.id === spellId)?.name ?? spellId;
  }

  /** Highest circle `activeClassIndex` can cast at the character's current level in it. */
  function maxAvailableCircle(): number {
    if (!activeClassDetail || !activeClassOption) return 0;
    const classLevel = classes.find(
      (c) => c.class_definition_id === activeClassOption.id,
    )?.level;
    const slots =
      activeClassDetail.levels.find((l) => l.level === classLevel)?.spell_slots ?? [];
    const available = slots.filter((s) => s.slot_count > 0).map((s) => s.spell_level);
    return available.length > 0 ? Math.max(...available) : 0;
  }

  const grouped = new Map<number, CharacterSpell[]>();
  for (const spell of spells) {
    const list = grouped.get(spell.level) ?? [];
    list.push(spell);
    grouped.set(spell.level, list);
  }
  const circles = [...grouped.keys()].sort((a, b) => a - b);

  async function addSpellNow(spell: SpellSummary) {
    setError(null);
    try {
      await addSpell.mutateAsync({
        spell_id: spell.id,
        source_class: activeClassIndex,
      });
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Não foi possível adicionar a magia.",
      );
    }
  }

  /**
   * Cantrips are always eligible; a leveled spell above what the active
   * class can cast at the character's current level asks for confirmation
   * first — complementary to the backend's known/prepared-limit check
   * (Fase 6), not a replacement for it.
   */
  async function handleAdd(spell: SpellSummary) {
    if (spell.level > 0 && spell.level > maxAvailableCircle()) {
      setPendingAddSpell(spell);
      return;
    }
    await addSpellNow(spell);
  }

  async function handleConfirmAdd() {
    if (!pendingAddSpell) return;
    const spell = pendingAddSpell;
    setPendingAddSpell(null);
    await addSpellNow(spell);
  }

  async function handleTogglePrepared(spell: CharacterSpell) {
    setError(null);
    setTogglingId(spell.id);
    try {
      await updateSpell.mutateAsync({
        spellEntryId: spell.id,
        data: { prepared: !spell.prepared },
      });
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Não foi possível preparar a magia.",
      );
    } finally {
      setTogglingId(null);
    }
  }

  async function handleRemove(spell: CharacterSpell) {
    setError(null);
    try {
      await removeSpell.mutateAsync(spell.id);
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Não foi possível remover a magia.",
      );
    }
  }

  function availableCastLevels(spellLevel: number): number[] {
    return spellSlots
      .filter((slot) => slot.spell_level >= spellLevel && slot.used < slot.max)
      .map((slot) => slot.spell_level)
      .sort((a, b) => a - b);
  }

  /** The spell's own level if it has a slot, else the lowest level that does. */
  function defaultCastLevel(spell: CharacterSpell): number {
    const available = availableCastLevels(spell.level);
    return available.includes(spell.level) ? spell.level : (available[0] ?? spell.level);
  }

  async function handleCast(spell: CharacterSpell, options: { asRitual?: boolean } = {}) {
    setError(null);
    try {
      await castSpell.mutateAsync({
        spellEntryId: spell.id,
        data: options.asRitual
          ? { as_ritual: true }
          : { cast_at_level: castLevelBySpell[spell.id] ?? defaultCastLevel(spell) },
      });
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Não foi possível conjurar a magia.",
      );
    }
  }

  return (
    <section aria-label="Magias" className="space-y-4 rounded-lg border border-border bg-card p-4">
      <h2 className="font-semibold">Magias</h2>

      {circles.length === 0 ? (
        <p className="text-sm text-muted-foreground">Nenhuma magia conhecida.</p>
      ) : (
        circles.map((level) => (
          <details key={level} open>
            <summary className="cursor-pointer list-none text-xs font-semibold uppercase text-muted-foreground marker:content-none">
              <h3 className="inline">{circleLabel(level)}</h3>
            </summary>
            <ul className="mt-1 divide-y divide-border">
              {grouped.get(level)?.map((spell) => (
                <li key={spell.id} className="py-2">
                  <div className="flex items-center justify-between gap-2">
                    <button
                      type="button"
                      onClick={() =>
                        setExpandedId(expandedId === spell.id ? null : spell.id)
                      }
                      className="text-left text-sm hover:underline"
                    >
                      {nameFor(spell.spell_id)}
                      {spell.ritual ? (
                        <span className="ml-1 text-xs text-muted-foreground">
                          (ritual)
                        </span>
                      ) : null}
                    </button>
                    <div className="flex items-center gap-2 text-xs">
                      <button
                        type="button"
                        onClick={() => handleTogglePrepared(spell)}
                        disabled={togglingId === spell.id}
                        className={
                          spell.prepared
                            ? "text-primary hover:underline"
                            : "text-muted-foreground hover:underline"
                        }
                      >
                        {spell.prepared ? "preparada" : "preparar"}
                      </button>
                      <button
                        type="button"
                        onClick={() => handleRemove(spell)}
                        disabled={removeSpell.isPending}
                        className="text-destructive hover:underline"
                      >
                        remover
                      </button>
                    </div>
                  </div>
                  {level > 0 ? (
                    <CastControls
                      spell={spell}
                      availableLevels={availableCastLevels(spell.level)}
                      castLevel={castLevelBySpell[spell.id] ?? defaultCastLevel(spell)}
                      onCastLevelChange={(newLevel) =>
                        setCastLevelBySpell((prev) => ({ ...prev, [spell.id]: newLevel }))
                      }
                      onCast={() => handleCast(spell)}
                      onCastAsRitual={
                        spell.ritual ? () => handleCast(spell, { asRitual: true }) : undefined
                      }
                      isPending={castSpell.isPending}
                    />
                  ) : null}
                  <SpellRollControls
                    characterId={characterId}
                    spell={spell}
                    spellName={nameFor(spell.spell_id)}
                    castAtLevel={
                      level > 0 ? (castLevelBySpell[spell.id] ?? defaultCastLevel(spell)) : 0
                    }
                  />
                  {expandedId === spell.id ? <SpellDetail spellId={spell.spell_id} /> : null}
                </li>
              ))}
            </ul>
          </details>
        ))
      )}

      <div className="space-y-2 border-t border-border pt-3">
        <p className="text-xs text-muted-foreground">Adicionar magia</p>
        {classOptions.length > 1 ? (
          <select
            value={activeClassIndex ?? ""}
            onChange={(e) => setSourceClassIndex(e.target.value)}
            aria-label="Classe conjuradora"
            className="rounded-md border border-input bg-background px-2 py-1.5 text-sm"
          >
            {classOptions.map((c) => (
              <option key={c.id} value={c.index ?? ""}>
                {c.name}
              </option>
            ))}
          </select>
        ) : null}
        <SpellSearch
          campaignId={campaignId}
          classIndex={activeClassIndex}
          excludeSpellIds={new Set(spells.map((s) => s.spell_id))}
          onSelect={handleAdd}
        />
      </div>

      {error ? (
        <p role="alert" className="text-sm text-destructive">
          {error}
        </p>
      ) : null}

      <ConfirmDialog
        open={pendingAddSpell !== null}
        title="Círculo indisponível"
        description={
          pendingAddSpell
            ? `${pendingAddSpell.name} é de um círculo que ${
                activeClassOption?.name ?? "esta classe"
              } ainda não conjura neste nível. Adicionar mesmo assim?`
            : undefined
        }
        confirmLabel="Adicionar mesmo assim"
        onConfirm={handleConfirmAdd}
        onCancel={() => setPendingAddSpell(null)}
      />
    </section>
  );
}

/**
 * Cast controls for one non-cantrip spell: a level selector (only when more
 * than one slot level is available, for upcasting), a "conjurar" button
 * (disabled with an explanatory tooltip when no slot is available), and a
 * "conjurar como ritual" button when the spell allows it (never disabled —
 * a ritual cast never consumes a slot).
 */
function CastControls({
  spell,
  availableLevels,
  castLevel,
  onCastLevelChange,
  onCast,
  onCastAsRitual,
  isPending,
}: {
  spell: CharacterSpell;
  availableLevels: number[];
  castLevel: number;
  onCastLevelChange: (level: number) => void;
  onCast: () => void;
  onCastAsRitual?: () => void;
  isPending: boolean;
}) {
  const hasSlot = availableLevels.length > 0;

  return (
    <div className="mt-1 flex items-center gap-2 text-xs">
      {availableLevels.length > 1 ? (
        <select
          value={castLevel}
          onChange={(e) => onCastLevelChange(Number(e.target.value))}
          aria-label={`Nível de conjuração de ${spell.spell_id}`}
          className="rounded-md border border-input bg-background px-1 py-0.5 text-xs"
        >
          {availableLevels.map((level) => (
            <option key={level} value={level}>
              {circleLabel(level)}
            </option>
          ))}
        </select>
      ) : null}
      <button
        type="button"
        onClick={onCast}
        disabled={!hasSlot || isPending}
        title={hasSlot ? undefined : "Nenhum slot disponível"}
        className="rounded border border-border px-2 py-0.5 hover:bg-secondary disabled:opacity-40"
      >
        conjurar
      </button>
      {onCastAsRitual ? (
        <button
          type="button"
          onClick={onCastAsRitual}
          disabled={isPending}
          className="rounded border border-border px-2 py-0.5 hover:bg-secondary disabled:opacity-40"
        >
          conjurar como ritual
        </button>
      ) : null}
    </div>
  );
}

/**
 * "Atacar" / "CD" / "Dano" for a known spell, straight from the sheet —
 * mirrors `WeaponAttackButton` (equipment-list.tsx): each roll/reveal is
 * fired by hand, resolved by `GET .../attack-profile` at `castAtLevel` so
 * an upcast spell's damage matches whatever level "conjurar" is set to.
 * Which buttons show comes from the catalog spell alone (`action_type`,
 * whether it has any damage rows) — no fetch needed just to decide that.
 */
function SpellRollControls({
  characterId,
  spell,
  spellName,
  castAtLevel,
}: {
  characterId: string;
  spell: CharacterSpell;
  spellName: string;
  castAtLevel: number;
}) {
  const { data: catalogSpell } = useCatalogEntry("spells", spell.spell_id);
  const attackProfile = useSpellAttackProfile(characterId);
  const roll = useRoll();
  const rollDamage = useRollDamage();
  const [error, setError] = useState<string | null>(null);
  const [revealedDc, setRevealedDc] = useState<string | null>(null);

  if (!catalogSpell) return null;
  const showAttack = catalogSpell.action_type === "attack_roll";
  const showSaveDc = catalogSpell.action_type === "saving_throw";
  const showDamage = catalogSpell.damages.length > 0;
  if (!showAttack && !showSaveDc && !showDamage) return null;

  async function handleRoll(kind: "attack" | "save" | "damage") {
    setError(null);
    try {
      const profile = await attackProfile.mutateAsync({
        spellEntryId: spell.id,
        castAtLevel,
      });
      if (kind === "attack") {
        roll(`${spellName} (ataque)`, profile.attack_bonus);
      } else if (kind === "save") {
        const ability = profile.save_ability ? ABILITY_LABELS[profile.save_ability] : null;
        setRevealedDc(
          profile.save_dc != null
            ? `CD ${profile.save_dc}${ability ? ` (${ability})` : ""}`
            : "CD indisponível",
        );
      } else if (profile.damage_dice) {
        rollDamage(`${spellName} (dano)`, profile.damage_dice, 0);
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Não foi possível rolar.");
    }
  }

  return (
    <div className="mt-1 flex flex-wrap items-center gap-2 text-xs">
      {showAttack ? (
        <button
          type="button"
          onClick={() => handleRoll("attack")}
          disabled={attackProfile.isPending}
          className="rounded border border-border px-2 py-0.5 hover:bg-secondary disabled:opacity-40"
        >
          atacar
        </button>
      ) : null}
      {showSaveDc ? (
        <button
          type="button"
          onClick={() => handleRoll("save")}
          disabled={attackProfile.isPending}
          className="rounded border border-border px-2 py-0.5 hover:bg-secondary disabled:opacity-40"
        >
          {revealedDc ?? "ver CD"}
        </button>
      ) : null}
      {showDamage ? (
        <button
          type="button"
          onClick={() => handleRoll("damage")}
          disabled={attackProfile.isPending}
          className="rounded border border-border px-2 py-0.5 hover:bg-secondary disabled:opacity-40"
        >
          dano
        </button>
      ) : null}
      {error ? <span className="text-destructive">{error}</span> : null}
    </div>
  );
}

function SpellDetail({ spellId }: { spellId: string }) {
  const { data: spell, isLoading } = useCatalogEntry("spells", spellId);
  if (isLoading || !spell) {
    return <p className="mt-1 text-xs text-muted-foreground">Carregando…</p>;
  }
  return (
    <div className="mt-1 space-y-1 text-xs text-muted-foreground">
      <p>
        {spell.casting_time} · {spell.range} · {spell.duration} · {spell.components}
      </p>
      <p>{spell.description}</p>
    </div>
  );
}
