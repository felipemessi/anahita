"use client";

import { useState, type FormEvent } from "react";

import { useCreateCustomEntry } from "@/hooks/use-catalog";
import { ApiError } from "@/lib/api/client";
import type { CatalogDetailByCategory } from "@/lib/api/catalog";
import type { CatalogCategory } from "@/types/catalog";

interface FieldConfig {
  key: string;
  label: string;
  type: "text" | "number" | "textarea";
  required?: boolean;
}

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
    { key: "school", label: "Escola", type: "text", required: true },
    { key: "casting_time", label: "Tempo de conjuração", type: "text" },
    { key: "range", label: "Alcance", type: "text" },
    { key: "duration", label: "Duração", type: "text" },
    { key: "components", label: "Componentes", type: "text" },
  ],
  equipment: [
    { key: "item_type", label: "Tipo", type: "text", required: true },
    { key: "weight", label: "Peso", type: "number" },
    { key: "cost", label: "Custo", type: "number" },
  ],
  monsters: [
    { key: "size", label: "Tamanho", type: "text", required: true },
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
          ? "O backend ainda não aceita criação de homebrew nesta categoria."
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
