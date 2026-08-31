import type { Background } from "@/types/catalog";

/** Structured detail view for a `Background` — replaces the generic JSON dump (Fase 11). */
export function BackgroundDetail({ background }: { background: Background }) {
  return (
    <div className="space-y-4">
      <dl className="grid grid-cols-1 gap-3 text-sm sm:grid-cols-2">
        <div>
          <dt className="text-muted-foreground">Traços de Personalidade</dt>
          <dd className="whitespace-pre-line">{background.personality_traits || "—"}</dd>
        </div>
        <div>
          <dt className="text-muted-foreground">Ideais</dt>
          <dd className="whitespace-pre-line">{background.ideals || "—"}</dd>
        </div>
        <div>
          <dt className="text-muted-foreground">Vínculos</dt>
          <dd className="whitespace-pre-line">{background.bonds || "—"}</dd>
        </div>
        <div>
          <dt className="text-muted-foreground">Fraquezas</dt>
          <dd className="whitespace-pre-line">{background.flaws || "—"}</dd>
        </div>
      </dl>

      {background.proficiencies.length > 0 ? (
        <p className="text-sm">
          <span className="font-medium">Proficiências: </span>
          {background.proficiencies.length} concedida(s)
        </p>
      ) : null}

      {background.equipment.length > 0 ? (
        <section>
          <h3 className="font-semibold">Equipamento Inicial</h3>
          <ul className="mt-1 space-y-1 text-sm">
            {background.equipment.map((equipment) => (
              <li key={equipment.id}>
                {equipment.item_name} × {equipment.quantity}
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {background.feature ? (
        <section>
          <h3 className="font-semibold">Característica</h3>
          <p className="mt-1 text-sm">
            <span className="font-medium">{background.feature.feature_name}. </span>
            {background.feature.description}
          </p>
        </section>
      ) : null}
    </div>
  );
}
