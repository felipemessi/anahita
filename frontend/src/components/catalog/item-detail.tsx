import type { Item } from "@/types/catalog";

/** Structured detail view for an `Item` (equipment) — replaces the generic JSON dump (Fase 11). */
export function ItemDetail({ item }: { item: Item }) {
  return (
    <div className="space-y-4">
      <p className="whitespace-pre-line text-sm">{item.description}</p>

      <dl className="grid grid-cols-2 gap-2 text-sm sm:grid-cols-4">
        <div>
          <dt className="text-muted-foreground">Tipo</dt>
          <dd className="capitalize">{item.item_type}</dd>
        </div>
        <div>
          <dt className="text-muted-foreground">Categoria</dt>
          <dd>{item.equipment_category}</dd>
        </div>
        <div>
          <dt className="text-muted-foreground">Peso (kg)</dt>
          <dd>{item.weight}</dd>
        </div>
        <div>
          <dt className="text-muted-foreground">Custo (po)</dt>
          <dd>{item.cost}</dd>
        </div>
        {item.rarity ? (
          <div>
            <dt className="text-muted-foreground">Raridade</dt>
            <dd className="capitalize">{item.rarity}</dd>
          </div>
        ) : null}
      </dl>

      {item.properties.length > 0 ? (
        <p className="text-sm">
          <span className="font-medium">Propriedades: </span>
          {item.properties.map((property) => property.name).join(", ")}
        </p>
      ) : null}

      {item.weapon_detail ? (
        <section>
          <h3 className="font-semibold">Detalhes de Arma</h3>
          <dl className="mt-1 grid grid-cols-3 gap-2 text-sm">
            <div>
              <dt className="text-muted-foreground">Dano</dt>
              <dd className="font-mono">{item.weapon_detail.damage_dice}</dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Tipo de Dano</dt>
              <dd className="capitalize">{item.weapon_detail.damage_type}</dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Alcance</dt>
              <dd>{item.weapon_detail.weapon_range}</dd>
            </div>
          </dl>
        </section>
      ) : null}

      {item.armor_detail ? (
        <section>
          <h3 className="font-semibold">Detalhes de Armadura</h3>
          <dl className="mt-1 grid grid-cols-2 gap-2 text-sm sm:grid-cols-4">
            <div>
              <dt className="text-muted-foreground">CA Base</dt>
              <dd>{item.armor_detail.base_ac}</dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Limite de Bônus de DES</dt>
              <dd>{item.armor_detail.dex_bonus_cap ?? "Sem limite"}</dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Desvantagem em Furtividade</dt>
              <dd>{item.armor_detail.stealth_disadvantage ? "Sim" : "Não"}</dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Força Mínima</dt>
              <dd>{item.armor_detail.strength_requirement ?? "—"}</dd>
            </div>
          </dl>
        </section>
      ) : null}
    </div>
  );
}
