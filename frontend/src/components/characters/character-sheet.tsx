"use client";

import { useState } from "react";

import { AbilityScores } from "@/components/characters/ability-scores";
import { SkillList } from "@/components/characters/skill-list";
import { SpellSlots } from "@/components/characters/spell-slots";
import { useUpdateCharacterHp } from "@/hooks/use-character";
import { calculateModifier } from "@/lib/utils/dnd-rules";
import type { Character } from "@/types/character";

/**
 * Full character sheet (PRD §9.3): header, ability scores, skills, combat
 * (AC/HP editable inline/speed/initiative), spells, equipment, features.
 * Equipment/features aren't modeled on `Character` yet — placeholders.
 */
export function CharacterSheet({ character }: { character: Character }) {
  const updateHp = useUpdateCharacterHp(character.id);
  const [hpDraft, setHpDraft] = useState(String(character.hit_point_current));
  const [hpError, setHpError] = useState<string | null>(null);

  const dexScore = character.ability_scores.find((s) => s.ability === "dex");
  const initiative = dexScore ? calculateModifier(dexScore.base_score + dexScore.asi_bonus + dexScore.misc_bonus) : 0;

  async function handleHpSubmit() {
    const value = Number(hpDraft);
    if (Number.isNaN(value)) return;
    setHpError(null);
    try {
      await updateHp.mutateAsync(value);
    } catch {
      setHpError("Não foi possível salvar o HP. Tente novamente.");
      setHpDraft(String(character.hit_point_current));
    }
  }

  return (
    <article className="space-y-6">
      <header>
        <h1 className="text-2xl font-bold">{character.name}</h1>
        <p className="text-sm text-muted-foreground">
          Nível {character.level}
          {character.background ? ` · ${character.background}` : ""}
          {character.alignment ? ` · ${character.alignment}` : ""}
        </p>
      </header>

      <AbilityScores scores={character.ability_scores} />

      <section aria-label="Combate" className="rounded-lg border border-border bg-card p-4">
        <h2 className="font-semibold">Combate</h2>
        <div className="mt-2 grid grid-cols-2 gap-3 sm:grid-cols-4">
          <div>
            <p className="text-xs text-muted-foreground">CA</p>
            <p className="font-mono text-lg">{character.armor_class}</p>
          </div>
          <div>
            <label htmlFor="hp-current" className="text-xs text-muted-foreground">
              PV atual
            </label>
            <div className="flex items-center gap-1">
              <input
                id="hp-current"
                type="number"
                value={hpDraft}
                onChange={(e) => setHpDraft(e.target.value)}
                onBlur={handleHpSubmit}
                className="w-16 rounded-md border border-input bg-background px-2 py-1 font-mono text-lg"
              />
              <span className="font-mono text-sm text-muted-foreground">
                / {character.hit_point_max}
              </span>
            </div>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Deslocamento</p>
            <p className="font-mono text-lg">{character.speed} ft</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Iniciativa</p>
            <p className="font-mono text-lg">
              {initiative >= 0 ? "+" : ""}
              {initiative}
            </p>
          </div>
        </div>
        {hpError ? (
          <p role="alert" className="mt-2 text-sm text-destructive">
            {hpError}
          </p>
        ) : null}
      </section>

      <SkillList skills={character.skills} />

      <SpellSlots />

      <section aria-label="Equipamento" className="rounded-lg border border-border bg-card p-4">
        <h2 className="font-semibold">Equipamento</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Em breve (backend ainda não modela inventário pessoal do personagem).
        </p>
      </section>

      <section aria-label="Características" className="rounded-lg border border-border bg-card p-4">
        <h2 className="font-semibold">Características</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Em breve (backend ainda não expõe features resolvidas por classe/raça/talento no personagem).
        </p>
      </section>
    </article>
  );
}
