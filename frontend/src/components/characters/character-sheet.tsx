"use client";

import { useState, type FormEvent } from "react";

import { AbilityScores } from "@/components/characters/ability-scores";
import { RollButton } from "@/components/characters/roll-button";
import { RollLogProvider } from "@/components/characters/roll-log";
import { SkillList } from "@/components/characters/skill-list";
import { SpellSlots } from "@/components/characters/spell-slots";
import { useCatalogList } from "@/hooks/use-catalog";
import {
  useAddCharacterEquipment,
  useAddCharacterFeature,
  useUpdateCharacterHp,
} from "@/hooks/use-character";
import { calculateModifier } from "@/lib/utils/dnd-rules";
import type { Character, FeatureSourceType } from "@/types/character";

/**
 * Full character sheet (PRD §9.3): header, ability scores, skills, combat
 * (AC/HP editable inline/speed/initiative), spells, equipment, features.
 */
export function CharacterSheet({
  campaignId,
  character,
}: {
  campaignId: string;
  character: Character;
}) {
  const updateHp = useUpdateCharacterHp(character.id);
  const [hpDraft, setHpDraft] = useState(String(character.hit_point_current));
  const [hpError, setHpError] = useState<string | null>(null);

  const dexScore = character.ability_scores.find((s) => s.ability === "dex");
  const initiative = dexScore
    ? calculateModifier(dexScore.base_score + dexScore.asi_bonus + dexScore.misc_bonus)
    : 0;

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
    <RollLogProvider>
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
              <RollButton
                label="Iniciativa"
                modifier={initiative}
                className="font-mono text-lg hover:text-primary hover:underline"
              />
            </div>
          </div>
          {hpError ? (
            <p role="alert" className="mt-2 text-sm text-destructive">
              {hpError}
            </p>
          ) : null}
        </section>

        <SkillList skills={character.skills} />

        <SpellSlots
          characterId={character.id}
          campaignId={campaignId}
          spells={character.spells}
        />

        <EquipmentSection
          characterId={character.id}
          campaignId={campaignId}
          equipment={character.equipment}
        />

        <FeaturesSection characterId={character.id} features={character.features} />
      </article>
    </RollLogProvider>
  );
}

function EquipmentSection({
  characterId,
  campaignId,
  equipment,
}: {
  characterId: string;
  campaignId: string;
  equipment: Character["equipment"];
}) {
  const { data: catalogItems } = useCatalogList("equipment", { campaign_id: campaignId });
  const addEquipment = useAddCharacterEquipment(characterId);
  const [itemId, setItemId] = useState("");
  const [error, setError] = useState<string | null>(null);

  function nameFor(id: string): string {
    return catalogItems?.find((i) => i.id === id)?.name ?? id;
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!itemId) return;
    setError(null);
    try {
      await addEquipment.mutateAsync({ item_id: itemId });
      setItemId("");
    } catch {
      setError("Não foi possível adicionar o item.");
    }
  }

  return (
    <section aria-label="Equipamento" className="rounded-lg border border-border bg-card p-4">
      <h2 className="font-semibold">Equipamento</h2>

      {equipment.length > 0 ? (
        <ul className="mt-2 space-y-1 text-sm">
          {equipment.map((entry) => (
            <li key={entry.id} className="flex items-center justify-between">
              <span>
                {nameFor(entry.item_id)}
                {entry.quantity > 1 ? ` (x${entry.quantity})` : ""}
              </span>
              {entry.equipped ? (
                <span className="text-xs text-primary">equipado</span>
              ) : null}
            </li>
          ))}
        </ul>
      ) : (
        <p className="mt-1 text-sm text-muted-foreground">Inventário vazio.</p>
      )}

      <form onSubmit={handleSubmit} className="mt-3 flex flex-wrap items-end gap-3">
        <div className="space-y-1">
          <label htmlFor="add-item" className="text-xs text-muted-foreground">
            Adicionar item
          </label>
          <select
            id="add-item"
            value={itemId}
            onChange={(e) => setItemId(e.target.value)}
            className="rounded-md border border-input bg-background px-2 py-1.5 text-sm"
          >
            <option value="">Selecione…</option>
            {catalogItems?.map((i) => (
              <option key={i.id} value={i.id}>
                {i.name}
              </option>
            ))}
          </select>
        </div>
        <button
          type="submit"
          disabled={!itemId || addEquipment.isPending}
          className="rounded-md border border-border px-3 py-1.5 text-sm hover:bg-secondary disabled:opacity-40"
        >
          Adicionar
        </button>
      </form>
      {error ? (
        <p role="alert" className="mt-1 text-sm text-destructive">
          {error}
        </p>
      ) : null}
    </section>
  );
}

function FeaturesSection({
  characterId,
  features,
}: {
  characterId: string;
  features: Character["features"];
}) {
  const addFeature = useAddCharacterFeature(characterId);
  const [sourceType, setSourceType] = useState<FeatureSourceType>("class");
  const [sourceName, setSourceName] = useState("");
  const [featureName, setFeatureName] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!sourceName || !featureName) return;
    setError(null);
    try {
      await addFeature.mutateAsync({
        source_type: sourceType,
        source_name: sourceName,
        feature_name: featureName,
      });
      setSourceName("");
      setFeatureName("");
    } catch {
      setError("Não foi possível adicionar a característica.");
    }
  }

  return (
    <section aria-label="Características" className="rounded-lg border border-border bg-card p-4">
      <h2 className="font-semibold">Características</h2>

      {features.length > 0 ? (
        <ul className="mt-2 space-y-1 text-sm">
          {features.map((feature) => (
            <li key={feature.id}>
              <span className="font-medium">{feature.feature_name}</span>{" "}
              <span className="text-xs text-muted-foreground">
                ({feature.source_name})
              </span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="mt-1 text-sm text-muted-foreground">Nenhuma característica registrada.</p>
      )}

      <form onSubmit={handleSubmit} className="mt-3 flex flex-wrap items-end gap-3">
        <div className="space-y-1">
          <label htmlFor="feature-source-type" className="text-xs text-muted-foreground">
            Origem
          </label>
          <select
            id="feature-source-type"
            value={sourceType}
            onChange={(e) => setSourceType(e.target.value as FeatureSourceType)}
            className="rounded-md border border-input bg-background px-2 py-1.5 text-sm"
          >
            <option value="class">Classe</option>
            <option value="feat">Talento</option>
          </select>
        </div>
        <div className="space-y-1">
          <label htmlFor="feature-source-name" className="text-xs text-muted-foreground">
            Nome da fonte
          </label>
          <input
            id="feature-source-name"
            value={sourceName}
            onChange={(e) => setSourceName(e.target.value)}
            placeholder="ex.: Fighter"
            className="rounded-md border border-input bg-background px-2 py-1.5 text-sm"
          />
        </div>
        <div className="space-y-1">
          <label htmlFor="feature-name" className="text-xs text-muted-foreground">
            Característica
          </label>
          <input
            id="feature-name"
            value={featureName}
            onChange={(e) => setFeatureName(e.target.value)}
            placeholder="ex.: Second Wind"
            className="rounded-md border border-input bg-background px-2 py-1.5 text-sm"
          />
        </div>
        <button
          type="submit"
          disabled={!sourceName || !featureName || addFeature.isPending}
          className="rounded-md border border-border px-3 py-1.5 text-sm hover:bg-secondary disabled:opacity-40"
        >
          Adicionar
        </button>
      </form>
      {error ? (
        <p role="alert" className="mt-1 text-sm text-destructive">
          {error}
        </p>
      ) : null}
    </section>
  );
}
