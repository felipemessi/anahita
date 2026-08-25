"use client";

import { useState } from "react";

import { useCatalogEntry, useCatalogList } from "@/hooks/use-catalog";
import { useCharacter } from "@/hooks/use-character";
import { useCombat } from "@/hooks/use-combat";
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

  const isFlavor = FLAVOR_ACTIONS.some((a) => a.type === kind);
  const needsTarget = !isFlavor;

  function handleDeclare() {
    const target_id = needsTarget ? targetId : participant.id;
    if (needsTarget && !target_id) return;

    switch (kind) {
      case "attack_weapon_equipped":
        declareAction({
          actionType: "attack_weapon",
          participant_id: participant.id,
          target_id,
          weapon_equipment_id: weaponEquipmentId || undefined,
          monster_action_id: monsterActionId || undefined,
        });
        return;
      case "attack_weapon_manual":
        declareAction({
          actionType: "attack_weapon",
          participant_id: participant.id,
          target_id,
          manual_attack_bonus: manualBonus === "" ? undefined : Number(manualBonus),
          manual_damage_expression: manualDamage || undefined,
        });
        return;
      case "attack_spell":
        declareAction({
          actionType: "attack_spell",
          participant_id: participant.id,
          target_id,
          spell_entry_id: spellEntryId || undefined,
        });
        return;
      case "grapple":
      case "shove":
        declareAction({ actionType: kind, participant_id: participant.id, target_id });
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

        <button
          type="button"
          onClick={handleDeclare}
          disabled={needsTarget && !targetId}
          className="rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground hover:opacity-90 disabled:opacity-50"
        >
          Declarar
        </button>
      </div>
    </section>
  );
}

function buildKindOptions(
  participant: EncounterParticipant,
): { value: string; label: string }[] {
  const options: { value: string; label: string }[] = [];
  if (participant.character_id || participant.monster_id) {
    options.push({ value: "attack_weapon_equipped", label: "Atacar com arma equipada" });
  }
  options.push({ value: "attack_weapon_manual", label: "Atacar manualmente" });
  if (participant.character_id) {
    options.push({ value: "attack_spell", label: "Conjurar magia" });
  }
  options.push({ value: "grapple", label: "Agarrar" });
  options.push({ value: "shove", label: "Empurrar" });
  for (const flavor of FLAVOR_ACTIONS) {
    options.push({ value: flavor.type, label: flavor.label });
  }
  return options;
}
