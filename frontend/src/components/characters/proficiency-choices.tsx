"use client";

import { useEffect, useState } from "react";

import { SKILL_LABELS } from "@/components/characters/skill-list";
import { useProficiencyChoices, useSetProficiencyChoices } from "@/hooks/use-character";
import { ApiError } from "@/lib/api/client";
import type { CharacterProficiencyChoiceGroup, Skill } from "@/types/character";

/**
 * One "choose N of [...]" skill proficiency group (Fase 10): options already
 * chosen (`group.selected`) render checked and disabled — the backend has no
 * way to un-set a skill proficiency once granted, so treat a prior choice as
 * locked, same as a race/class's fixed grant. The remaining budget
 * (`choose_count - selected.length`) caps how many *new* options the player
 * may check before submitting.
 */
function ProficiencyChoiceGroupFieldset({
  group,
  draft,
  onToggle,
}: {
  group: CharacterProficiencyChoiceGroup;
  draft: Set<Skill>;
  onToggle: (skill: Skill) => void;
}) {
  const remaining = group.choose_count - group.selected.length - draft.size;
  const locked = group.selected.length >= group.choose_count;

  return (
    <fieldset className="rounded-md border border-border p-3">
      <legend className="px-1 text-sm font-medium">
        Escolha {group.choose_count} de:
      </legend>
      {!locked ? (
        <p className="text-xs text-muted-foreground">
          {remaining > 0
            ? `Faltam ${remaining} escolha(s).`
            : "Seleção completa — clique em Salvar para confirmar."}
        </p>
      ) : null}
      <ul className="mt-2 space-y-1">
        {group.options.map((skill) => {
          const alreadySelected = group.selected.includes(skill);
          const checked = alreadySelected || draft.has(skill);
          const disabled =
            alreadySelected || (!draft.has(skill) && remaining <= 0);
          const inputId = `proficiency-choice-${group.id}-${skill}`;
          return (
            <li key={skill} className="flex items-center gap-2 text-sm">
              <input
                id={inputId}
                type="checkbox"
                checked={checked}
                disabled={disabled}
                onChange={() => onToggle(skill)}
                className="h-4 w-4 rounded border-input"
              />
              <label
                htmlFor={inputId}
                className={alreadySelected ? "text-muted-foreground" : ""}
              >
                {SKILL_LABELS[skill] ?? skill}
                {alreadySelected ? (
                  <span className="ml-1 text-xs">(já escolhida)</span>
                ) : null}
              </label>
            </li>
          );
        })}
      </ul>
    </fieldset>
  );
}

/**
 * Proficiency choice UI (PRD frontend backlog Fase 10): renders every
 * "choose N of [...]" skill group the character's race/class(es) actually
 * offer (`GET /characters/{id}/proficiencies`), in place of a free-text
 * field. Nothing is rendered when the character has no choice group at all
 * (e.g. every race/class proficiency it has is a fixed grant).
 */
export function ProficiencyChoices({ characterId }: { characterId: string }) {
  const { data: groups } = useProficiencyChoices(characterId);
  const setChoices = useSetProficiencyChoices(characterId);
  const [draftByGroup, setDraftByGroup] = useState<Record<string, Set<Skill>>>({});
  const [error, setError] = useState<string | null>(null);

  // Reset drafts whenever the server's group data changes (e.g. after a
  // successful submit resolves `selected`) so a confirmed pick doesn't stay
  // double-counted as both `selected` and still-drafted.
  useEffect(() => {
    setDraftByGroup({});
  }, [groups]);

  if (!groups || groups.length === 0) return null;

  const pendingGroups = groups.filter(
    (group) => group.selected.length < group.choose_count,
  );
  if (pendingGroups.length === 0) return null;

  function toggleSkill(groupId: string, skill: Skill) {
    setDraftByGroup((prev) => {
      const current = new Set(prev[groupId] ?? []);
      if (current.has(skill)) {
        current.delete(skill);
      } else {
        current.add(skill);
      }
      return { ...prev, [groupId]: current };
    });
  }

  const draftedSkills = Object.values(draftByGroup).flatMap((set) => [...set]);
  const hasDraft = draftedSkills.length > 0;

  async function handleSubmit() {
    if (!hasDraft) return;
    setError(null);
    try {
      await setChoices.mutateAsync({ skills: [...new Set(draftedSkills)] });
      setDraftByGroup({});
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Não foi possível salvar as proficiências.",
      );
    }
  }

  return (
    <section
      aria-label="Escolha de proficiências"
      className="rounded-lg border border-border bg-card p-4"
    >
      <h2 className="font-semibold">Escolha de proficiências</h2>
      <p className="mt-1 text-xs text-muted-foreground">
        Selecione as perícias entre as opções que sua raça/classe oferecem.
      </p>
      <div className="mt-3 space-y-3">
        {pendingGroups.map((group) => (
          <ProficiencyChoiceGroupFieldset
            key={group.id}
            group={group}
            draft={draftByGroup[group.id] ?? new Set<Skill>()}
            onToggle={(skill) => toggleSkill(group.id, skill)}
          />
        ))}
      </div>

      {error ? (
        <p role="alert" className="mt-2 text-sm text-destructive">
          {error}
        </p>
      ) : null}

      <button
        type="button"
        onClick={handleSubmit}
        disabled={!hasDraft || setChoices.isPending}
        className="mt-3 rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground hover:opacity-90 disabled:opacity-40"
      >
        Salvar
      </button>
    </section>
  );
}
