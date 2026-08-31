"use client";

import { useState } from "react";

import { ClassResources } from "@/components/characters/class-resources";
import { RollButton } from "@/components/characters/roll-button";
import { useAbilityScores, useCatalogEntry, useCatalogList } from "@/hooks/use-catalog";
import { useCastCharacterSpell, useCharacter } from "@/hooks/use-character";
import { useCombat } from "@/hooks/use-combat";
import { calculateModifier } from "@/lib/utils/dnd-rules";
import type { Monster } from "@/types/catalog";
import type { CombatActionType, EncounterParticipant } from "@/types/combat";

const FLAVOR_ACTIONS: { type: CombatActionType; label: string }[] = [
  { type: "dash", label: "Disparada" },
  { type: "dodge", label: "Esquivar" },
  { type: "disengage", label: "Desengajar" },
  { type: "help", label: "Ajudar" },
  { type: "hide", label: "Esconder-se" },
  { type: "ready", label: "Preparar" },
  { type: "search", label: "Procurar" },
];

/**
 * The action options for the current-turn participant: attack (equipped
 * weapon, manual, or spell), grapple/shove, and the flavor actions with
 * nothing to roll — resolved server-side via `declare_action`, result
 * appearing in the combat log in real time over the same WS connection
 * (backlog Fase 6 frontend, história 5).
 */
export function ActionPicker({
  campaignId,
  participant,
  otherParticipants,
}: {
  campaignId: string;
  participant: EncounterParticipant;
  otherParticipants: EncounterParticipant[];
}) {
  const { declareAction } = useCombat();
  const { data: character } = useCharacter(participant.character_id ?? "");
  const { data: monster } = useCatalogEntry("monsters", participant.monster_id ?? "");
  const { data: catalogItems } = useCatalogList("equipment", { campaign_id: campaignId });
  const { data: catalogSpells } = useCatalogList("spells", { campaign_id: campaignId });
  const castSpell = useCastCharacterSpell(character?.id ?? "");

  function itemName(itemId: string): string {
    return catalogItems?.find((i) => i.id === itemId)?.name ?? itemId;
  }
  function spellName(spellId: string): string {
    return catalogSpells?.find((s) => s.id === spellId)?.name ?? spellId;
  }

  const kindOptions = buildKindOptions(participant);
  const [kind, setKind] = useState(kindOptions[0]?.value ?? "grapple");
  const [targetId, setTargetId] = useState(otherParticipants[0]?.id ?? "");
  const [weaponEquipmentId, setWeaponEquipmentId] = useState("");
  const [spellEntryId, setSpellEntryId] = useState("");
  const [monsterActionId, setMonsterActionId] = useState("");
  const [manualBonus, setManualBonus] = useState("");
  const [manualDamage, setManualDamage] = useState("");
  const [showManualRoll, setShowManualRoll] = useState(false);
  const [manualAttackRoll, setManualAttackRoll] = useState("");
  const [manualDamageRoll, setManualDamageRoll] = useState("");
  const [manualTargetRoll, setManualTargetRoll] = useState("");

  // "cast_spell_effect": a non-attack spell (saving_throw/cast_only), cast
  // straight from the character's own known spells (POST .../spells/{id}/cast)
  // — separate from "attack_spell", which stays on the declare_action/combat
  // log path (Fase 6). Fase 8.
  const [effectSpellEntryId, setEffectSpellEntryId] = useState("");
  const [effectTargetId, setEffectTargetId] = useState("");
  const [castResult, setCastResult] = useState<{
    saveDc: number;
    saveAbilityScoreId: string;
    targetParticipantId: string | null;
  } | null>(null);

  const isCastEffect = kind === "cast_spell_effect";
  const effectEntry = character?.spells.find((s) => s.id === effectSpellEntryId);
  const { data: effectSpellDetail } = useCatalogEntry("spells", effectEntry?.spell_id ?? "");
  const effectTargetType = effectSpellDetail?.target_type ?? null;
  const effectNeedsTarget = isCastEffect && effectTargetType !== null && effectTargetType !== "self";
  // A `cast_only` spell *with* a target (heal/direct damage, e.g. Cure
  // Wounds) is declared through the combat action flow instead of the
  // sheet-only cast endpoint (Fase 12) — that's the path the backend
  // actually applies the effect through (`_resolve_spell_effect`, via
  // `attack_spell`); the sheet endpoint stays bookkeeping-only even with a
  // target_participant_id. A self-only/no-target cast_only spell (e.g.
  // Mage Armor) has nothing to apply to anyone, so it keeps using the
  // sheet endpoint. `saving_throw` spells are unaffected — they keep the
  // DC-display + manual-resolution flow below, unchanged.
  const isCastOnlyEffect = isCastEffect && effectSpellDetail?.action_type === "cast_only";
  const castOnlyGoesThroughCombat = isCastOnlyEffect && effectNeedsTarget;
  const [effectManualRoll, setEffectManualRoll] = useState("");

  const isFlavor = FLAVOR_ACTIONS.some((a) => a.type === kind);
  const isContest = kind === "grapple" || kind === "shove";
  const needsTarget = !isFlavor && !isCastEffect;
  const canRollManually = !isFlavor && !isCastEffect;

  async function handleCastEffect() {
    if (!effectSpellEntryId) return;
    if (castOnlyGoesThroughCombat) {
      if (!effectTargetId) return;
      declareAction({
        actionType: "attack_spell",
        participant_id: participant.id,
        target_id: effectTargetId,
        spell_entry_id: effectSpellEntryId,
        manual_damage_roll: effectManualRoll === "" ? undefined : Number(effectManualRoll),
      });
      setEffectManualRoll("");
      return;
    }
    setCastResult(null);
    const response = await castSpell.mutateAsync({
      spellEntryId: effectSpellEntryId,
      data: {
        target_participant_id: effectNeedsTarget ? effectTargetId || undefined : undefined,
      },
    });
    if (response.save_dc !== null && effectSpellDetail?.save_ability_score_id) {
      setCastResult({
        saveDc: response.save_dc,
        saveAbilityScoreId: effectSpellDetail.save_ability_score_id,
        targetParticipantId: response.target_participant_id,
      });
    }
  }

  function handleDeclare() {
    if (isCastEffect) return;
    const target_id = needsTarget ? targetId : participant.id;
    if (needsTarget && !target_id) return;

    // "digitar manualmente" is always an alternative to the server's roll,
    // never the default — these stay undefined (letting the server roll)
    // unless the DM/player explicitly typed something in.
    const manual_attack_roll =
      manualAttackRoll === "" ? undefined : Number(manualAttackRoll);
    const manual_damage_roll =
      manualDamageRoll === "" ? undefined : Number(manualDamageRoll);
    const manual_target_roll =
      manualTargetRoll === "" ? undefined : Number(manualTargetRoll);

    switch (kind) {
      case "attack_weapon_equipped":
        declareAction({
          actionType: "attack_weapon",
          participant_id: participant.id,
          target_id,
          weapon_equipment_id: weaponEquipmentId || undefined,
          monster_action_id: monsterActionId || undefined,
          manual_attack_roll,
          manual_damage_roll,
        });
        return;
      case "attack_weapon_manual":
        declareAction({
          actionType: "attack_weapon",
          participant_id: participant.id,
          target_id,
          manual_attack_bonus: manualBonus === "" ? undefined : Number(manualBonus),
          manual_damage_expression: manualDamage || undefined,
          manual_attack_roll,
          manual_damage_roll,
        });
        return;
      case "attack_spell":
        declareAction({
          actionType: "attack_spell",
          participant_id: participant.id,
          target_id,
          spell_entry_id: spellEntryId || undefined,
          manual_attack_roll,
          manual_damage_roll,
        });
        return;
      case "grapple":
      case "shove":
        declareAction({
          actionType: kind,
          participant_id: participant.id,
          target_id,
          manual_attack_roll,
          manual_target_roll,
        });
        return;
      default:
        declareAction({
          actionType: kind as CombatActionType,
          participant_id: participant.id,
          target_id,
        });
    }
  }

  return (
    <section aria-label="Declarar ação" className="rounded-lg border border-border bg-card p-4">
      <h2 className="font-semibold">Ação de {participant.name}</h2>

      {character?.resources && character.resources.length > 0 ? (
        <div className="mt-2">
          <ClassResources
            characterId={character.id}
            resources={character.resources}
            combat={{ participantId: participant.id, otherParticipants, declareAction }}
          />
        </div>
      ) : null}

      <div className="mt-2 flex flex-wrap items-end gap-3">
        <div className="space-y-1">
          <label htmlFor="action-kind" className="text-xs text-muted-foreground">
            Ação
          </label>
          <select
            id="action-kind"
            value={kind}
            onChange={(e) => setKind(e.target.value)}
            className="rounded-md border border-input bg-background px-2 py-1.5 text-sm"
          >
            {kindOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        {needsTarget ? (
          <div className="space-y-1">
            <label htmlFor="action-target" className="text-xs text-muted-foreground">
              Alvo
            </label>
            <select
              id="action-target"
              value={targetId}
              onChange={(e) => setTargetId(e.target.value)}
              className="rounded-md border border-input bg-background px-2 py-1.5 text-sm"
            >
              <option value="">Selecione…</option>
              {otherParticipants.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </div>
        ) : null}

        {kind === "attack_weapon_equipped" && character ? (
          <div className="space-y-1">
            <label htmlFor="action-weapon" className="text-xs text-muted-foreground">
              Arma
            </label>
            <select
              id="action-weapon"
              value={weaponEquipmentId}
              onChange={(e) => setWeaponEquipmentId(e.target.value)}
              className="rounded-md border border-input bg-background px-2 py-1.5 text-sm"
            >
              <option value="">Selecione…</option>
              {character.equipment
                .filter((e) => e.equipped)
                .map((e) => (
                    <option key={e.id} value={e.id}>
                    {itemName(e.item_id)}
                  </option>
                ))}
            </select>
          </div>
        ) : null}

        {kind === "attack_weapon_equipped" && monster ? (
          <div className="space-y-1">
            <label htmlFor="action-monster" className="text-xs text-muted-foreground">
              Ação do monstro
            </label>
            <select
              id="action-monster"
              value={monsterActionId}
              onChange={(e) => setMonsterActionId(e.target.value)}
              className="rounded-md border border-input bg-background px-2 py-1.5 text-sm"
            >
              <option value="">Selecione…</option>
              {monster.actions.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.name}
                </option>
              ))}
            </select>
          </div>
        ) : null}

        {kind === "attack_weapon_manual" ? (
          <>
            <div className="space-y-1">
              <label htmlFor="action-manual-bonus" className="text-xs text-muted-foreground">
                Bônus de ataque
              </label>
              <input
                id="action-manual-bonus"
                type="number"
                value={manualBonus}
                onChange={(e) => setManualBonus(e.target.value)}
                className="w-20 rounded-md border border-input bg-background px-2 py-1.5 text-sm"
              />
            </div>
            <div className="space-y-1">
              <label htmlFor="action-manual-damage" className="text-xs text-muted-foreground">
                Dano (ex.: 1d8+3)
              </label>
              <input
                id="action-manual-damage"
                value={manualDamage}
                onChange={(e) => setManualDamage(e.target.value)}
                className="w-28 rounded-md border border-input bg-background px-2 py-1.5 text-sm"
              />
            </div>
          </>
        ) : null}

        {kind === "attack_spell" && character ? (
          <div className="space-y-1">
            <label htmlFor="action-spell" className="text-xs text-muted-foreground">
              Magia
            </label>
            <select
              id="action-spell"
              value={spellEntryId}
              onChange={(e) => setSpellEntryId(e.target.value)}
              className="rounded-md border border-input bg-background px-2 py-1.5 text-sm"
            >
              <option value="">Selecione…</option>
              {character.spells.map((s) => (
                <option key={s.id} value={s.id}>
                  {spellName(s.spell_id)}
                </option>
              ))}
            </select>
          </div>
        ) : null}

        {isCastEffect && character ? (
          <div className="space-y-1">
            <label htmlFor="action-effect-spell" className="text-xs text-muted-foreground">
              Magia
            </label>
            <select
              id="action-effect-spell"
              value={effectSpellEntryId}
              onChange={(e) => {
                setEffectSpellEntryId(e.target.value);
                setCastResult(null);
              }}
              className="rounded-md border border-input bg-background px-2 py-1.5 text-sm"
            >
              <option value="">Selecione…</option>
              {character.spells.map((s) => (
                <option key={s.id} value={s.id}>
                  {spellName(s.spell_id)}
                </option>
              ))}
            </select>
          </div>
        ) : null}

        {effectNeedsTarget ? (
          <div className="space-y-1">
            <label htmlFor="action-effect-target" className="text-xs text-muted-foreground">
              Alvo
            </label>
            <select
              id="action-effect-target"
              value={effectTargetId}
              onChange={(e) => setEffectTargetId(e.target.value)}
              className="rounded-md border border-input bg-background px-2 py-1.5 text-sm"
            >
              <option value="">Selecione…</option>
              {otherParticipants.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </div>
        ) : null}

        {castOnlyGoesThroughCombat ? (
          <div className="space-y-1">
            <label htmlFor="action-effect-manual-roll" className="text-xs text-muted-foreground">
              {effectTargetType === "ally" ? "Cura rolada (ex.: 1d8+3)" : "Dano rolado"}
            </label>
            <input
              id="action-effect-manual-roll"
              type="number"
              value={effectManualRoll}
              onChange={(e) => setEffectManualRoll(e.target.value)}
              placeholder="Deixe em branco pra rolagem automática, se houver"
              className="w-56 rounded-md border border-input bg-background px-2 py-1.5 text-sm"
            />
          </div>
        ) : null}

        {isCastEffect && effectSpellDetail?.action_type === "attack_roll" ? (
          <p className="text-xs text-amber-500">
            Essa magia é de ataque — use &quot;Conjurar magia (ataque)&quot; em vez disso.
          </p>
        ) : null}

        <button
          type="button"
          onClick={isCastEffect ? handleCastEffect : handleDeclare}
          disabled={
            isCastEffect
              ? !effectSpellEntryId ||
                effectSpellDetail?.action_type === "attack_roll" ||
                (effectNeedsTarget && !effectTargetId) ||
                (!castOnlyGoesThroughCombat && castSpell.isPending)
              : needsTarget && !targetId
          }
          className="rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground hover:opacity-90 disabled:opacity-50"
        >
          Declarar
        </button>
      </div>

      {castResult ? (
        <SpellSaveCallout
          dc={castResult.saveDc}
          saveAbilityScoreId={castResult.saveAbilityScoreId}
          targetParticipant={otherParticipants.find(
            (p) => p.id === castResult.targetParticipantId,
          )}
        />
      ) : null}

      {canRollManually ? (
        <div className="mt-2">
          <button
            type="button"
            onClick={() => setShowManualRoll((v) => !v)}
            className="text-xs text-muted-foreground underline"
          >
            {showManualRoll ? "Usar rolagem automática" : "Digitar rolagem manualmente"}
          </button>
          {showManualRoll ? (
            <div className="mt-2 flex flex-wrap items-end gap-3">
              <div className="space-y-1">
                <label htmlFor="manual-attack-roll" className="text-xs text-muted-foreground">
                  {isContest ? "Teste do atacante" : "Resultado do ataque"}
                </label>
                <input
                  id="manual-attack-roll"
                  type="number"
                  value={manualAttackRoll}
                  onChange={(e) => setManualAttackRoll(e.target.value)}
                  className="w-20 rounded-md border border-input bg-background px-2 py-1.5 text-sm"
                />
              </div>
              {isContest ? (
                <div className="space-y-1">
                  <label htmlFor="manual-target-roll" className="text-xs text-muted-foreground">
                    Teste do alvo
                  </label>
                  <input
                    id="manual-target-roll"
                    type="number"
                    value={manualTargetRoll}
                    onChange={(e) => setManualTargetRoll(e.target.value)}
                    className="w-20 rounded-md border border-input bg-background px-2 py-1.5 text-sm"
                  />
                </div>
              ) : (
                <div className="space-y-1">
                  <label htmlFor="manual-damage-roll" className="text-xs text-muted-foreground">
                    Resultado do dano
                  </label>
                  <input
                    id="manual-damage-roll"
                    type="number"
                    value={manualDamageRoll}
                    onChange={(e) => setManualDamageRoll(e.target.value)}
                    className="w-20 rounded-md border border-input bg-background px-2 py-1.5 text-sm"
                  />
                </div>
              )}
            </div>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}

/**
 * The DC of a just-cast `saving_throw` spell, plus a click-to-roll shortcut
 * for the target's save — resolves `saveAbilityScoreId` (a
 * `Spell.save_ability_score_id`) to its ability code via `useAbilityScores`
 * (Fase 8), same modifier-resolution pattern as
 * `ParticipantCard`'s concentration-save callout.
 */
function SpellSaveCallout({
  dc,
  saveAbilityScoreId,
  targetParticipant,
}: {
  dc: number;
  saveAbilityScoreId: string;
  targetParticipant: EncounterParticipant | undefined;
}) {
  const { data: abilityScores } = useAbilityScores();
  const { data: targetCharacter } = useCharacter(targetParticipant?.character_id ?? "");
  const { data: targetMonster } = useCatalogEntry(
    "monsters",
    targetParticipant?.monster_id ?? "",
  );

  const abilityIndex = abilityScores?.find((a) => a.id === saveAbilityScoreId)?.index;
  const ability = targetCharacter?.ability_scores.find((s) => s.ability === abilityIndex);
  const modifier =
    ability?.save_bonus ??
    (targetMonster && abilityIndex
      ? calculateModifier(MONSTER_ABILITY_SCORE[abilityIndex]?.(targetMonster) ?? 10)
      : 0);
  const label = ABILITY_SAVE_LABEL[abilityIndex ?? ""] ?? "Resistência";

  return (
    <p className="mt-2 flex items-center gap-2 text-xs font-medium text-amber-500">
      <span>
        CD {dc}
        {targetParticipant ? ` (${targetParticipant.name})` : ""}
      </span>
      <RollButton label={label} modifier={modifier} className="underline hover:text-foreground" />
    </p>
  );
}

const ABILITY_SAVE_LABEL: Record<string, string> = {
  str: "Resistência de Força",
  dex: "Resistência de Destreza",
  con: "Resistência de Constituição",
  int: "Resistência de Inteligência",
  wis: "Resistência de Sabedoria",
  cha: "Resistência de Carisma",
};

/** A catalog monster's raw ability score, keyed by short ability code. */
const MONSTER_ABILITY_SCORE: Record<string, (m: Monster) => number> = {
  str: (m) => m.strength,
  dex: (m) => m.dexterity,
  con: (m) => m.constitution,
  int: (m) => m.intelligence,
  wis: (m) => m.wisdom,
  cha: (m) => m.charisma,
};

function buildKindOptions(
  participant: EncounterParticipant,
): { value: string; label: string }[] {
  const options: { value: string; label: string }[] = [];
  if (participant.character_id || participant.monster_id) {
    options.push({ value: "attack_weapon_equipped", label: "Atacar com arma equipada" });
  }
  options.push({ value: "attack_weapon_manual", label: "Atacar manualmente" });
  if (participant.character_id) {
    options.push({ value: "attack_spell", label: "Conjurar magia (ataque)" });
    options.push({ value: "cast_spell_effect", label: "Conjurar magia (efeito)" });
  }
  options.push({ value: "grapple", label: "Agarrar" });
  options.push({ value: "shove", label: "Empurrar" });
  for (const flavor of FLAVOR_ACTIONS) {
    options.push({ value: flavor.type, label: flavor.label });
  }
  return options;
}
