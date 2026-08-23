import { MonsterStatBlock } from "@/components/catalog/monster-stat-block";
import type { CatalogDetailByCategory } from "@/lib/api/catalog";
import type { CatalogCategory, Monster } from "@/types/catalog";

interface EntryLike {
  name: string;
  is_custom: boolean;
  description?: string;
}

/**
 * Detail view for a single catalog entry. Monsters render the full
 * `monster-stat-block.tsx`; every other category gets a generic
 * name/description + raw field dump (v1 — see backlog note on Fase 1 for
 * follow-up work rendering each category's own shape, e.g. race traits,
 * class progression tables, spell components).
 */
export function CatalogEntryDetail<C extends CatalogCategory>({
  category,
  entry,
}: {
  category: C;
  entry: CatalogDetailByCategory[C];
}) {
  if (category === "monsters") {
    return <MonsterStatBlock monster={entry as Monster} />;
  }

  const generic = entry as unknown as EntryLike;
  const { name, is_custom: isCustom, description } = generic;
  const rest: Record<string, unknown> = { ...entry };
  delete rest.name;
  delete rest.is_custom;
  delete rest.description;

  return (
    <article className="space-y-4 rounded-lg border border-border bg-card p-4">
      <header className="flex items-center justify-between">
        <h2 className="text-xl font-bold">{name}</h2>
        <span
          className={`rounded-full px-2 py-0.5 text-xs ${
            isCustom
              ? "bg-secondary text-secondary-foreground"
              : "border border-border text-muted-foreground"
          }`}
        >
          {isCustom ? "Homebrew" : "SRD"}
        </span>
      </header>

      {description ? (
        <p className="whitespace-pre-line text-sm">{description}</p>
      ) : null}

      <details className="text-sm">
        <summary className="cursor-pointer text-muted-foreground">
          Detalhes técnicos
        </summary>
        <pre className="mt-2 overflow-x-auto rounded-md bg-muted p-3 text-xs">
          {JSON.stringify(rest, null, 2)}
        </pre>
      </details>
    </article>
  );
}
