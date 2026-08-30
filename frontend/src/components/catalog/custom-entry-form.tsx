"use client";

import { useState, type FormEvent } from "react";

import { useCreateCustomEntry } from "@/hooks/use-catalog";
import { ApiError } from "@/lib/api/client";
import type { CatalogDetailByCategory } from "@/lib/api/catalog";
import type { CatalogCategory, CreatureSize, ItemType, SpellSchool } from "@/types/catalog";

import { RaceHomebrewForm } from "./race-homebrew-form";

interface FieldConfig {
  key: string;
  label: string;
  type: "text" | "number" | "textarea" | "select";
  required?: boolean;
  /** Options for `type: "select"` — mirrors the backend enum (catalog/domain.py). */
  options?: readonly string[];
}

/** `Monster.size` — a native DB enum, must match exactly (see `MonsterCreate.size`). */
const CREATURE_SIZES: readonly CreatureSize[] = [
  "tiny",
  "small",
  "medium",
  "large",
  "huge",
  "gargantuan",
];

/** `Item.item_type` — validated against `ItemType` on the backend. */
const ITEM_TYPES: readonly ItemType[] = ["weapon", "armor", "gear", "tool", "consumable"];

/** `Spell.school` — must match an existing `MagicSchool.index` (fixed SRD vocabulary). */
const SPELL_SCHOOLS: readonly SpellSchool[] = [
  "abjuration",
  "conjuration",
  "divination",
  "enchantment",
  "evocation",
  "illusion",
  "necromancy",
  "transmutation",
];

const COMMON_FIELDS: FieldConfig[] = [
  { key: "name", label: "Nome", type: "text", required: true },
  { key: "description", label: "Descrição", type: "textarea" },
];

/**
 * Category-specific fields beyond name/description, for every category with
 * a homebrew-creation endpoint (backlog Fase 1). `rules` and `backgrounds`
 * don't use the common `description` field — their backend schema has no
 * such field — so they're excluded via `OMIT_COMMON_KEYS` below.
 */
const EXTRA_FIELDS: Partial<Record<CatalogCategory, FieldConfig[]>> = {
  classes: [
    { key: "hit_die", label: "Dado de vida", type: "number", required: true },
    { key: "primary_ability", label: "Habilidade primária", type: "text", required: true },
  ],
  spells: [
    { key: "level", label: "Nível", type: "number", required: true },
    { key: "school", label: "Escola", type: "select", required: true, options: SPELL_SCHOOLS },
    { key: "casting_time", label: "Tempo de conjuração", type: "text" },
    { key: "range", label: "Alcance", type: "text" },
    { key: "duration", label: "Duração", type: "text" },
    { key: "components", label: "Componentes", type: "text" },
  ],
  equipment: [
    { key: "item_type", label: "Tipo", type: "select", required: true, options: ITEM_TYPES },
    { key: "weight", label: "Peso", type: "number" },
    { key: "cost", label: "Custo", type: "number" },
  ],
  monsters: [
    { key: "size", label: "Tamanho", type: "select", required: true, options: CREATURE_SIZES },
    { key: "creature_type", label: "Tipo de criatura", type: "text", required: true },
    { key: "alignment", label: "Alinhamento", type: "text" },
    { key: "hit_points", label: "Pontos de vida", type: "number", required: true },
    { key: "challenge_rating", label: "Desafio (CR)", type: "number", required: true },
  ],
  "magic-items": [{ key: "rarity", label: "Raridade", type: "text" }],
  backgrounds: [
    { key: "personality_traits", label: "Traços de personalidade", type: "textarea" },
    { key: "ideals", label: "Ideais", type: "textarea" },
    { key: "bonds", label: "Vínculos", type: "textarea" },
    { key: "flaws", label: "Defeitos", type: "textarea" },
  ],
  rules: [{ key: "desc", label: "Descrição", type: "textarea" }],
};

/** Categories whose backend schema has no `description` field. */
const OMIT_COMMON_KEYS: Partial<Record<CatalogCategory, string[]>> = {
  backgrounds: ["description"],
  rules: ["description"],
};

/**
 * Extract a user-facing message from an API error. FastAPI's 422 validation
 * errors carry `detail` as a list of `{loc, msg, ...}` objects rather than a
 * string, so `ApiError.message` falls back to the generic HTTP status text
 * for those — surface the real per-field messages instead when available.
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
 * Homebrew creation form for a catalog category, always scoped to the
 * current campaign — `campaign_id` is never a form field, it's injected
 * automatically by `useCreateCustomEntry` from the current route.
 */
export function CustomEntryForm<C extends CatalogCategory>({
  category,
  campaignId,
  onCreated,
}: {
  category: C;
  campaignId: string;
  onCreated?: (entry: CatalogDetailByCategory[C]) => void;
}) {
  // Races carry structured attachments (language/proficiency multi-select at
  // creation, plus ability-bonus/trait/subrace follow-up calls once the race
  // exists) that don't fit this form's "one text/number/select field per
  // key" model — delegate entirely to a dedicated sub-form instead of
  // growing EXTRA_FIELDS/handleSubmit with race-only branches (Fase 11).
  //
  // This dispatch happens before any hook is called in this component (and
  // `category` never changes across a mounted form instance — each route
  // renders one fixed category), so the two branches below never violate
  // the Rules of Hooks against each other.
  if (category === "races") {
    return (
      <RaceHomebrewForm
        campaignId={campaignId}
        onCreated={onCreated as ((race: CatalogDetailByCategory["races"]) => void) | undefined}
      />
    );
  }
  return <GenericCatalogEntryForm category={category} campaignId={campaignId} onCreated={onCreated} />;
}

function GenericCatalogEntryForm<C extends CatalogCategory>({
  category,
  campaignId,
  onCreated,
}: {
  category: C;
  campaignId: string;
  onCreated?: (entry: CatalogDetailByCategory[C]) => void;
}) {
  const omitKeys: string[] =
    (OMIT_COMMON_KEYS as Record<string, string[] | undefined>)[category] ?? [];
  const fields = [
    ...COMMON_FIELDS.filter((f) => !omitKeys.includes(f.key)),
    ...(EXTRA_FIELDS[category] ?? []),
  ];
  const [values, setValues] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);
  const createEntry = useCreateCustomEntry(category, campaignId);

  function setValue(key: string, value: string) {
    setValues((prev) => ({ ...prev, [key]: value }));
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    const payload: Record<string, unknown> = {};
    for (const field of fields) {
      const raw = values[field.key] ?? "";
      payload[field.key] = field.type === "number" ? Number(raw) : raw;
    }

    try {
      const entry = await createEntry.mutateAsync(payload);
      setValues({});
      onCreated?.(entry);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? apiErrorMessage(err)
          : "Não foi possível criar a entrada. Tente novamente.",
      );
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {fields.map((field) => (
        <div key={field.key} className="space-y-1">
          <label htmlFor={`entry-${field.key}`} className="text-sm font-medium">
            {field.label}
          </label>
          {field.type === "textarea" ? (
            <textarea
              id={`entry-${field.key}`}
              required={field.required}
              value={values[field.key] ?? ""}
              onChange={(e) => setValue(field.key, e.target.value)}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              rows={3}
            />
          ) : field.type === "select" ? (
            <select
              id={`entry-${field.key}`}
              required={field.required}
              value={values[field.key] ?? ""}
              onChange={(e) => setValue(field.key, e.target.value)}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            >
              <option value="" disabled>
                Selecione…
              </option>
              {field.options?.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          ) : (
            <input
              id={`entry-${field.key}`}
              type={field.type}
              required={field.required}
              value={values[field.key] ?? ""}
              onChange={(e) => setValue(field.key, e.target.value)}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            />
          )}
        </div>
      ))}

      {error ? (
        <p role="alert" className="text-sm text-destructive">
          {error}
        </p>
      ) : null}

      <button
        type="submit"
        disabled={createEntry.isPending}
        className="w-full rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-opacity hover:opacity-90 disabled:opacity-60"
      >
        {createEntry.isPending ? "Criando…" : "Criar homebrew"}
      </button>
    </form>
  );
}
