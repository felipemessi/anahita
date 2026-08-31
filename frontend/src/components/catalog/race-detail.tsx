import type { Race } from "@/types/catalog";

/** Structured detail view for a `Race` — replaces the generic JSON dump (Fase 11). */
export function RaceDetail({ race }: { race: Race }) {
  return (
    <div className="space-y-4">
      <p className="whitespace-pre-line text-sm">{race.description}</p>

      <dl className="grid grid-cols-2 gap-2 text-sm sm:grid-cols-4">
        <div>
          <dt className="text-muted-foreground">Tamanho</dt>
          <dd className="capitalize">{race.size}</dd>
        </div>
        <div>
          <dt className="text-muted-foreground">Deslocamento (m)</dt>
          <dd>{race.speed}</dd>
        </div>
        <div>
          <dt className="text-muted-foreground">Visão no escuro (m)</dt>
          <dd>{race.darkvision_range || "—"}</dd>
        </div>
        <div>
          <dt className="text-muted-foreground">Idade</dt>
          <dd>{race.age || "—"}</dd>
        </div>
      </dl>

      {race.alignment_desc ? (
        <p className="text-sm">
          <span className="font-medium">Tendência: </span>
          {race.alignment_desc}
        </p>
      ) : null}

      {race.language_desc ? (
        <p className="text-sm">
          <span className="font-medium">Idiomas: </span>
          {race.language_desc}
        </p>
      ) : null}

      {race.ability_bonuses.length > 0 ? (
        <section>
          <h3 className="font-semibold">Bônus de Atributo</h3>
          <ul className="mt-1 flex flex-wrap gap-2 text-sm">
            {race.ability_bonuses.map((bonus) => (
              <li
                key={bonus.id}
                className="rounded-md border border-border px-2 py-1 font-mono uppercase"
              >
                {bonus.ability} +{bonus.bonus}
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {race.traits.length > 0 ? (
        <section>
          <h3 className="font-semibold">Traços</h3>
          <ul className="mt-1 space-y-2">
            {race.traits.map((trait) => (
              <li key={trait.id} className="text-sm">
                <span className="font-medium">{trait.trait_name}. </span>
                {trait.description}
                {trait.mechanical_effect ? (
                  <p className="text-xs text-muted-foreground">
                    Efeito mecânico: {trait.mechanical_effect}
                  </p>
                ) : null}
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {race.subraces.length > 0 ? (
        <section>
          <h3 className="font-semibold">Sub-raças</h3>
          <ul className="mt-2 space-y-3">
            {race.subraces.map((subrace) => (
              <li key={subrace.id} className="rounded-md border border-border p-3 text-sm">
                <p className="font-medium">{subrace.name}</p>
                <p className="mt-1 whitespace-pre-line">{subrace.description}</p>
                {subrace.ability_bonuses.length > 0 ? (
                  <ul className="mt-2 flex flex-wrap gap-2">
                    {subrace.ability_bonuses.map((bonus) => (
                      <li
                        key={bonus.id}
                        className="rounded-md border border-border px-2 py-1 font-mono text-xs uppercase"
                      >
                        {bonus.ability} +{bonus.bonus}
                      </li>
                    ))}
                  </ul>
                ) : null}
                {subrace.traits.length > 0 ? (
                  <ul className="mt-2 space-y-1">
                    {subrace.traits.map((trait) => (
                      <li key={trait.id}>
                        <span className="font-medium">{trait.trait_name}. </span>
                        {trait.description}
                      </li>
                    ))}
                  </ul>
                ) : null}
              </li>
            ))}
          </ul>
        </section>
      ) : null}
    </div>
  );
}
