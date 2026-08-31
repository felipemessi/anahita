"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { BackgroundDetail } from "@/components/catalog/background-detail";
import { ClassDetail } from "@/components/catalog/class-detail";
import { FeatDetail } from "@/components/catalog/feat-detail";
import { ItemDetail } from "@/components/catalog/item-detail";
import { MagicItemDetail } from "@/components/catalog/magic-item-detail";
import { MonsterStatBlock } from "@/components/catalog/monster-stat-block";
import { RaceDetail } from "@/components/catalog/race-detail";
import { RuleDetail } from "@/components/catalog/rule-detail";
import { SpellDetail } from "@/components/catalog/spell-detail";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { useMyMembership } from "@/hooks/use-campaign";
import { useDeleteCustomEntry } from "@/hooks/use-catalog";
import { ApiError } from "@/lib/api/client";
import type { CatalogDetailByCategory } from "@/lib/api/catalog";
import type {
  Background,
  CatalogCategory,
  ClassDefinition,
  Feat,
  Item,
  MagicItem,
  Monster,
  Race,
  Rule,
  Spell,
} from "@/types/catalog";

interface EntryLike {
  id: string;
  name: string;
  is_custom: boolean;
  description?: string;
}

/**
 * Detail view for a single catalog entry. Routes to a dedicated component per
 * category (Fase 11) — each renders its own shape (race traits, class
 * progression tables, spell components, …) instead of a raw field dump. Only
 * categories without a dedicated component yet fall back to the generic
 * name/description + JSON dump.
 *
 * Also owns the DM-only "excluir" action for homebrew entries: SRD content
 * (`is_custom=false`) never shows the button, and neither does a non-DM
 * member of `campaignId`.
 */
export function CatalogEntryDetail<C extends CatalogCategory>({
  category,
  entry,
  campaignId,
}: {
  category: C;
  entry: CatalogDetailByCategory[C];
  campaignId: string;
}) {
  const generic = entry as unknown as EntryLike;

  return (
    <div className="space-y-4">
      <EntryHeader entry={generic} category={category} campaignId={campaignId} />
      <CategoryBody category={category} entry={entry} />
    </div>
  );
}

function CategoryBody<C extends CatalogCategory>({
  category,
  entry,
}: {
  category: C;
  entry: CatalogDetailByCategory[C];
}) {
  switch (category) {
    case "races":
      return <RaceDetail race={entry as Race} />;
    case "classes":
      return <ClassDetail classDefinition={entry as ClassDefinition} />;
    case "spells":
      return <SpellDetail spell={entry as Spell} />;
    case "equipment":
      return <ItemDetail item={entry as Item} />;
    case "magic-items":
      return <MagicItemDetail magicItem={entry as MagicItem} />;
    case "monsters":
      return <MonsterStatBlock monster={entry as Monster} />;
    case "backgrounds":
      return <BackgroundDetail background={entry as Background} />;
    case "feats":
      return <FeatDetail feat={entry as Feat} />;
    case "rules":
      return <RuleDetail rule={entry as Rule} />;
    default:
      return <GenericBody entry={entry as unknown as EntryLike} />;
  }
}

/** Fallback for any category without a dedicated detail component yet. */
function GenericBody({ entry }: { entry: EntryLike }) {
  const rest: Record<string, unknown> = { ...entry };
  delete rest.id;
  delete rest.name;
  delete rest.is_custom;
  delete rest.description;

  return (
    <div className="space-y-4">
      {entry.description ? (
        <p className="whitespace-pre-line text-sm">{entry.description}</p>
      ) : null}

      <details className="text-sm">
        <summary className="cursor-pointer text-muted-foreground">
          Detalhes técnicos
        </summary>
        <pre className="mt-2 overflow-x-auto rounded-md bg-muted p-3 text-xs">
          {JSON.stringify(rest, null, 2)}
        </pre>
      </details>
    </div>
  );
}

function EntryHeader({
  entry,
  category,
  campaignId,
}: {
  entry: EntryLike;
  category: CatalogCategory;
  campaignId: string;
}) {
  const { data: membership } = useMyMembership(campaignId);
  const deleteEntry = useDeleteCustomEntry(category);
  const router = useRouter();
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canDelete = entry.is_custom && membership?.role === "dm";

  const handleConfirmDelete = async () => {
    try {
      await deleteEntry.mutateAsync(entry.id);
      setConfirmOpen(false);
      router.push(`/campaigns/${campaignId}/catalog/${category}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Não foi possível excluir a entrada.");
      setConfirmOpen(false);
    }
  };

  return (
    <header className="flex items-start justify-between gap-4 rounded-lg border border-border bg-card p-4">
      <div>
        <h2 className="text-xl font-bold">{entry.name}</h2>
        <span
          className={`mt-1 inline-block rounded-full px-2 py-0.5 text-xs ${
            entry.is_custom
              ? "bg-secondary text-secondary-foreground"
              : "border border-border text-muted-foreground"
          }`}
        >
          {entry.is_custom ? "Homebrew" : "SRD"}
        </span>
        {error ? <p className="mt-2 text-sm text-destructive">{error}</p> : null}
      </div>

      {canDelete ? (
        <button
          type="button"
          onClick={() => {
            setError(null);
            setConfirmOpen(true);
          }}
          className="shrink-0 rounded-md border border-destructive px-3 py-1.5 text-sm font-medium text-destructive hover:bg-destructive/10"
        >
          Excluir
        </button>
      ) : null}

      <ConfirmDialog
        open={confirmOpen}
        title={`Excluir "${entry.name}"?`}
        description="Esta ação não pode ser desfeita."
        confirmLabel="Excluir"
        onConfirm={() => void handleConfirmDelete()}
        onCancel={() => setConfirmOpen(false)}
      />
    </header>
  );
}
