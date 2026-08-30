"use client";

import { useState, type FormEvent } from "react";

import { useCreateCustomEntry, useLanguages, useProficiencies } from "@/hooks/use-catalog";
import { ApiError } from "@/lib/api/client";
import type { Race } from "@/types/catalog";

import { RaceAttachPanel } from "./race-attach-panel";

/** `Race.size` — a native DB enum on `RaceCreate.size`. */
const RACE_SIZES = ["tiny", "small", "medium", "large", "huge", "gargantuan"] as const;

/**
 * Extract a user-facing message from an API error, same behavior as
 * `custom-entry-form.tsx`'s `apiErrorMessage` — FastAPI's 422 `detail` is a
 * list of `{loc, msg, ...}` objects, not a string.
 */
function apiErrorMessage(err: ApiError): string {
  if (Array.isArray(err.detail)) {
    const messages = err.detail
      .map((item) =>
        item && typeof item === "object" && "msg" in item ? String(item.msg) : null,
      )
      .filter((msg): msg is string => msg !== null);
    if (messages.length > 0) return messages.join(" ");
  }
  return err.message;
}

/**
 * Dedicated homebrew-race form (Fase 11), used instead of the generic
 * `CustomEntryForm` field-list for `category === "races"`.
 *
 * Decision (documented per the backlog note): races carry structured
 * multi-select attachments (`language_ids`/`proficiency_ids` at creation,
 * plus ability bonuses/traits/subraces via follow-up `POST
 * /catalog/races/{id}/...` calls once the race exists) that don't fit the
 * generic form's "one text/number/select field per key" model. A dedicated
 * sub-form keeps that complexity out of `custom-entry-form.tsx` and out of
 * the other categories' (simpler) field lists.
 */
export function RaceHomebrewForm({
  campaignId,
  onCreated,
}: {
  campaignId: string;
  onCreated?: (race: Race) => void;
}) {
  const [values, setValues] = useState({
    name: "",
    description: "",
    age: "",
    alignment_desc: "",
    size_description: "",
    language_desc: "",
    speed: "30",
    size: "medium",
    darkvision_range: "0",
  });
  const [languageIds, setLanguageIds] = useState<Set<string>>(new Set());
  const [proficiencyIds, setProficiencyIds] = useState<Set<string>>(new Set());
  const [error, setError] = useState<string | null>(null);
  const [createdRace, setCreatedRace] = useState<Race | null>(null);

  const languagesQuery = useLanguages();
  const proficienciesQuery = useProficiencies();
  const createRace = useCreateCustomEntry("races", campaignId);

  function setValue(key: keyof typeof values, value: string) {
    setValues((prev) => ({ ...prev, [key]: value }));
  }

  function toggleId(set: Set<string>, setSet: (next: Set<string>) => void, id: string) {
    const next = new Set(set);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    setSet(next);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    const payload = {
      name: values.name,
      description: values.description,
      age: values.age,
      alignment_desc: values.alignment_desc,
      size_description: values.size_description,
      language_desc: values.language_desc,
      speed: Number(values.speed),
      size: values.size,
      darkvision_range: Number(values.darkvision_range),
      language_ids: Array.from(languageIds),
      proficiency_ids: Array.from(proficiencyIds),
    };

    try {
      const race = (await createRace.mutateAsync(payload)) as Race;
      setCreatedRace(race);
      onCreated?.(race);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? apiErrorMessage(err)
          : "Não foi possível criar a raça. Tente novamente.",
      );
    }
  }

  if (createdRace) {
    return <RaceAttachPanel race={createdRace} />;
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-1">
        <label htmlFor="race-name" className="text-sm font-medium">
          Nome
        </label>
        <input
          id="race-name"
          type="text"
          required
          value={values.name}
          onChange={(e) => setValue("name", e.target.value)}
          className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
        />
      </div>

      <div className="space-y-1">
        <label htmlFor="race-description" className="text-sm font-medium">
          Descrição
        </label>
        <textarea
          id="race-description"
          value={values.description}
          onChange={(e) => setValue("description", e.target.value)}
          rows={3}
          className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
        />
      </div>

      <div className="space-y-1">
        <label htmlFor="race-age" className="text-sm font-medium">
          Idade
        </label>
        <textarea
          id="race-age"
          value={values.age}
          onChange={(e) => setValue("age", e.target.value)}
          rows={2}
          className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
        />
      </div>

      <div className="space-y-1">
        <label htmlFor="race-alignment-desc" className="text-sm font-medium">
          Alinhamento (descrição)
        </label>
        <textarea
          id="race-alignment-desc"
          value={values.alignment_desc}
          onChange={(e) => setValue("alignment_desc", e.target.value)}
          rows={2}
          className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
        />
      </div>

      <div className="space-y-1">
        <label htmlFor="race-size-description" className="text-sm font-medium">
          Tamanho (descrição)
        </label>
        <textarea
          id="race-size-description"
          value={values.size_description}
          onChange={(e) => setValue("size_description", e.target.value)}
          rows={2}
          className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
        />
      </div>

      <div className="space-y-1">
        <label htmlFor="race-language-desc" className="text-sm font-medium">
          Idiomas (texto livre)
        </label>
        <textarea
          id="race-language-desc"
          value={values.language_desc}
          onChange={(e) => setValue("language_desc", e.target.value)}
          rows={2}
          placeholder="Ex.: um idioma adicional à sua escolha"
          className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
        />
      </div>

      <div className="grid grid-cols-3 gap-3">
        <div className="space-y-1">
          <label htmlFor="race-speed" className="text-sm font-medium">
            Deslocamento
          </label>
          <input
            id="race-speed"
            type="number"
            min={0}
            required
            value={values.speed}
            onChange={(e) => setValue("speed", e.target.value)}
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
          />
        </div>

        <div className="space-y-1">
          <label htmlFor="race-size" className="text-sm font-medium">
            Tamanho
          </label>
          <select
            id="race-size"
            required
            value={values.size}
            onChange={(e) => setValue("size", e.target.value)}
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
          >
            {RACE_SIZES.map((size) => (
              <option key={size} value={size}>
                {size}
              </option>
            ))}
          </select>
        </div>

        <div className="space-y-1">
          <label htmlFor="race-darkvision" className="text-sm font-medium">
            Visão no escuro
          </label>
          <input
            id="race-darkvision"
            type="number"
            min={0}
            required
            value={values.darkvision_range}
            onChange={(e) => setValue("darkvision_range", e.target.value)}
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
          />
        </div>
      </div>

      <fieldset className="rounded-md border border-border p-3">
        <legend className="px-1 text-sm font-medium">Idiomas concedidos</legend>
        <ul className="mt-2 grid grid-cols-2 gap-1 sm:grid-cols-3">
          {(languagesQuery.data ?? []).map((language) => {
            const inputId = `race-language-${language.id}`;
            return (
              <li key={language.id} className="flex items-center gap-2 text-sm">
                <input
                  id={inputId}
                  type="checkbox"
                  checked={languageIds.has(language.id)}
                  onChange={() => toggleId(languageIds, setLanguageIds, language.id)}
                  className="h-4 w-4 rounded border-input"
                />
                <label htmlFor={inputId}>{language.index ?? language.id}</label>
              </li>
            );
          })}
        </ul>
      </fieldset>

      <fieldset className="rounded-md border border-border p-3">
        <legend className="px-1 text-sm font-medium">Proficiências concedidas</legend>
        <ul className="mt-2 grid grid-cols-2 gap-1 sm:grid-cols-3">
          {(proficienciesQuery.data ?? []).map((proficiency) => {
            const inputId = `race-proficiency-${proficiency.id}`;
            return (
              <li key={proficiency.id} className="flex items-center gap-2 text-sm">
                <input
                  id={inputId}
                  type="checkbox"
                  checked={proficiencyIds.has(proficiency.id)}
                  onChange={() => toggleId(proficiencyIds, setProficiencyIds, proficiency.id)}
                  className="h-4 w-4 rounded border-input"
                />
                <label htmlFor={inputId}>{proficiency.index ?? proficiency.id}</label>
              </li>
            );
          })}
        </ul>
      </fieldset>

      {error ? (
        <p role="alert" className="text-sm text-destructive">
          {error}
        </p>
      ) : null}

      <button
        type="submit"
        disabled={createRace.isPending}
        className="w-full rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-opacity hover:opacity-90 disabled:opacity-60"
      >
        {createRace.isPending ? "Criando…" : "Criar raça homebrew"}
      </button>
    </form>
  );
}
