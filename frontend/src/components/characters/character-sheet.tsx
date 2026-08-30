"use client";

import { useEffect, useState, type FormEvent } from "react";

import { CatalogFilterBar } from "@/components/catalog/catalog-filter-bar";
import { AbilityScores } from "@/components/characters/ability-scores";
import { ClassResources } from "@/components/characters/class-resources";
import { ConcentrationIndicator } from "@/components/characters/concentration-indicator";
import { CharacterInfoEditor } from "@/components/characters/character-info-editor";
import { CurrencyTracker } from "@/components/characters/currency-tracker";
import { DeathSaveTracker } from "@/components/characters/death-save-tracker";
import { EquipmentList } from "@/components/characters/equipment-list";
import { HitDiceTracker } from "@/components/characters/hit-dice-tracker";
import { LevelUpDialog } from "@/components/characters/level-up-dialog";
import { PassiveScores } from "@/components/characters/passive-scores";
import { ProficiencyChoices } from "@/components/characters/proficiency-choices";
import { RollButton } from "@/components/characters/roll-button";
import { RollLogPanel, RollLogProvider } from "@/components/characters/roll-log";
import { SkillList } from "@/components/characters/skill-list";
import { SpellListByCircle } from "@/components/characters/spell-list-by-circle";
import { SpellSlots } from "@/components/characters/spell-slots";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { useCatalogFeature, useCatalogList } from "@/hooks/use-catalog";
import { useAddCharacterFeature, useRestCharacter, useUpdateCharacterHp } from "@/hooks/use-character";
import { ApiError } from "@/lib/api/client";
import { calculateModifier } from "@/lib/utils/dnd-rules";
import type { FeatSummary } from "@/types/catalog";
import type { Character, FeatureSourceType, RestType } from "@/types/character";

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
  const rest = useRestCharacter(character.id);
  const [restError, setRestError] = useState<string | null>(null);
  const [pendingRest, setPendingRest] = useState<RestType | null>(null);

  // Keep the "PV atual" input in sync when hit_point_current changes from
  // outside this input — a rest, spending hit dice, damage taken elsewhere
  // — not just from the initial mount value `useState` captured once.
  useEffect(() => {
    setHpDraft(String(character.hit_point_current));
  }, [character.hit_point_current]);

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

  async function handleRest(restType: RestType) {
    setRestError(null);
    try {
      await rest.mutateAsync({ rest_type: restType });
    } catch (err) {
      setRestError(
        err instanceof ApiError ? err.message : "Não foi possível descansar.",
      );
    }
  }

  async function handleConfirmRest() {
    if (!pendingRest) return;
    const restType = pendingRest;
    setPendingRest(null);
    await handleRest(restType);
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
          <div className="mt-2">
            <CharacterInfoEditor character={character} />
          </div>
        </header>

        <LevelUpDialog
          characterId={character.id}
          campaignId={campaignId}
          classes={character.classes}
        />

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
          <div className="mt-3 flex items-center gap-2">
            <button
              type="button"
              onClick={() => setPendingRest("short")}
              disabled={rest.isPending}
              className="rounded-md border border-border px-3 py-1.5 text-sm hover:bg-secondary disabled:opacity-40"
            >
              Descanso curto
            </button>
            <button
              type="button"
              onClick={() => setPendingRest("long")}
              disabled={rest.isPending}
              className="rounded-md border border-border px-3 py-1.5 text-sm hover:bg-secondary disabled:opacity-40"
            >
              Descanso longo
            </button>
          </div>
          {restError ? (
            <p role="alert" className="mt-2 text-sm text-destructive">
              {restError}
            </p>
          ) : null}
          <ConfirmDialog
            open={pendingRest !== null}
            title={pendingRest === "short" ? "Descanso curto" : "Descanso longo"}
            description="Isso pode resetar PV, espaços de magia e recursos de classe. Deseja continuar?"
            confirmLabel="Descansar"
            onConfirm={handleConfirmRest}
            onCancel={() => setPendingRest(null)}
          />
        </section>

        <DeathSaveTracker
          characterId={character.id}
          hitPointCurrent={character.hit_point_current}
          successes={character.death_save_successes}
          failures={character.death_save_failures}
          isDead={character.is_dead}
        />

        <ConcentrationIndicator
          characterId={character.id}
          concentratingSpellId={character.concentrating_spell_id}
        />

        <SkillList skills={character.skills} />

        <ProficiencyChoices characterId={character.id} />

        <PassiveScores
          passivePerception={character.passive_perception}
          passiveInvestigation={character.passive_investigation}
          passiveInsight={character.passive_insight}
        />

        <HitDiceTracker
          characterId={character.id}
          campaignId={campaignId}
          classes={character.classes}
        />

        <ClassResources characterId={character.id} resources={character.resources} />

        <SpellSlots slots={character.spell_slots} />

        <SpellListByCircle
          characterId={character.id}
          campaignId={campaignId}
          spells={character.spells}
          classes={character.classes}
          spellSlots={character.spell_slots}
        />

        <EquipmentList
          characterId={character.id}
          campaignId={campaignId}
          equipment={character.equipment}
        />

        <CurrencyTracker characterId={character.id} currencyCp={character.currency_cp} />

        <FeaturesSection
          characterId={character.id}
          campaignId={campaignId}
          features={character.features}
          featureChoices={character.feature_choices}
        />

        <RollLogPanel />
      </article>
    </RollLogProvider>
  );
}

/** One level-up choice picked, resolved to its option's name (Fase 8). */
function FeatureChoiceItem({ featureOptionId }: { featureOptionId: string }) {
  const { data: option } = useCatalogFeature(featureOptionId);
  if (!option) return null;
  return (
    <li>
      <span className="font-medium">{option.feature_name}</span>
    </li>
  );
}

export function FeaturesSection({
  characterId,
  campaignId,
  features,
  featureChoices,
}: {
  characterId: string;
  campaignId: string;
  features: Character["features"];
  featureChoices: Character["feature_choices"];
}) {
  const addFeature = useAddCharacterFeature(characterId);
  const [sourceType, setSourceType] = useState<FeatureSourceType>("class");
  const [sourceName, setSourceName] = useState("");
  const [featureName, setFeatureName] = useState("");
  const [featureDescription, setFeatureDescription] = useState<string | null>(null);
  const [featSearch, setFeatSearch] = useState("");
  const [error, setError] = useState<string | null>(null);

  const { data: catalogFeats } = useCatalogList("feats", { campaign_id: campaignId });
  const featResults = (catalogFeats ?? []).filter((f) =>
    f.name.toLowerCase().includes(featSearch.toLowerCase()),
  );

  function selectFeat(feat: FeatSummary) {
    setSourceName("Talento");
    setFeatureName(feat.name);
    setFeatureDescription(null);
  }

  function handleSourceTypeChange(next: FeatureSourceType) {
    setSourceType(next);
    setSourceName("");
    setFeatureName("");
    setFeatureDescription(null);
    setFeatSearch("");
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!sourceName || !featureName) return;
    setError(null);
    try {
      await addFeature.mutateAsync({
        source_type: sourceType,
        source_name: sourceName,
        feature_name: featureName,
        description: featureDescription,
      });
      setSourceName("");
      setFeatureName("");
      setFeatureDescription(null);
      setFeatSearch("");
    } catch {
      setError("Não foi possível adicionar a característica.");
    }
  }

  return (
    <section aria-label="Características" className="rounded-lg border border-border bg-card p-4">
      <h2 className="font-semibold">Características</h2>

      {features.length > 0 || featureChoices.length > 0 ? (
        <ul className="mt-2 space-y-1 text-sm">
          {features.map((feature) => (
            <li key={feature.id}>
              <span className="font-medium">{feature.feature_name}</span>{" "}
              <span className="text-xs text-muted-foreground">
                ({feature.source_name})
              </span>
            </li>
          ))}
          {featureChoices.map((choice) => (
            <FeatureChoiceItem key={choice.id} featureOptionId={choice.feature_option_id} />
          ))}
        </ul>
      ) : (
        <p className="mt-1 text-sm text-muted-foreground">Nenhuma característica registrada.</p>
      )}

      <form onSubmit={handleSubmit} className="mt-3 space-y-3">
        <div className="flex flex-wrap items-end gap-3">
          <div className="space-y-1">
            <label htmlFor="feature-source-type" className="text-xs text-muted-foreground">
              Origem
            </label>
            <select
              id="feature-source-type"
              value={sourceType}
              onChange={(e) => handleSourceTypeChange(e.target.value as FeatureSourceType)}
              className="rounded-md border border-input bg-background px-2 py-1.5 text-sm"
            >
              <option value="class">Classe</option>
              <option value="feat">Talento</option>
            </select>
          </div>

          {sourceType === "class" ? (
            <>
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
            </>
          ) : null}

          <button
            type="submit"
            disabled={!sourceName || !featureName || addFeature.isPending}
            className="rounded-md border border-border px-3 py-1.5 text-sm hover:bg-secondary disabled:opacity-40"
          >
            Adicionar
          </button>
        </div>

        {sourceType === "feat" ? (
          <div className="space-y-2">
            {featureName ? (
              <p className="text-sm">
                Talento selecionado: <span className="font-medium">{featureName}</span>{" "}
                <button
                  type="button"
                  onClick={() => {
                    setSourceName("");
                    setFeatureName("");
                  }}
                  className="text-xs text-muted-foreground underline"
                >
                  trocar
                </button>
              </p>
            ) : (
              <>
                <CatalogFilterBar search={featSearch} onSearchChange={setFeatSearch} />
                <ul className="max-h-48 divide-y divide-border overflow-y-auto rounded-md border border-border">
                  {featResults.length === 0 ? (
                    <li className="px-2 py-1.5 text-xs text-muted-foreground">
                      Nenhum talento encontrado.
                    </li>
                  ) : (
                    featResults.map((feat) => (
                      <li key={feat.id}>
                        <button
                          type="button"
                          onClick={() => selectFeat(feat)}
                          className="w-full px-2 py-1.5 text-left text-sm hover:bg-secondary/40"
                        >
                          {feat.name}
                        </button>
                      </li>
                    ))
                  )}
                </ul>
              </>
            )}
          </div>
        ) : null}
      </form>
      {error ? (
        <p role="alert" className="mt-1 text-sm text-destructive">
          {error}
        </p>
      ) : null}
    </section>
  );
}
