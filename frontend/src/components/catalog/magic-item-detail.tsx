import type { MagicItem } from "@/types/catalog";

/** Structured detail view for a `MagicItem` — replaces the generic JSON dump (Fase 11). */
export function MagicItemDetail({ magicItem }: { magicItem: MagicItem }) {
  return (
    <div className="space-y-4">
      <p className="whitespace-pre-line text-sm">{magicItem.description}</p>

      <dl className="grid grid-cols-2 gap-2 text-sm sm:grid-cols-3">
        <div>
          <dt className="text-muted-foreground">Categoria</dt>
          <dd>{magicItem.equipment_category}</dd>
        </div>
        <div>
          <dt className="text-muted-foreground">Raridade</dt>
          <dd className="capitalize">{magicItem.rarity}</dd>
        </div>
        <div>
          <dt className="text-muted-foreground">Variante</dt>
          <dd>{magicItem.is_variant ? "Sim" : "Não"}</dd>
        </div>
      </dl>

      {magicItem.variants.length > 0 ? (
        <section>
          <h3 className="font-semibold">Variantes</h3>
          <ul className="mt-1 space-y-1 text-sm">
            {magicItem.variants.map((variant) => (
              <li key={variant.id}>
                {variant.name} <span className="text-muted-foreground">({variant.rarity})</span>
              </li>
            ))}
          </ul>
        </section>
      ) : null}
    </div>
  );
}
