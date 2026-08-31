import type { ClassDefinition } from "@/types/catalog";

/** Structured detail view for a `ClassDefinition` — replaces the generic JSON dump (Fase 11). */
export function ClassDetail({ classDefinition }: { classDefinition: ClassDefinition }) {
  return (
    <div className="space-y-4">
      <dl className="grid grid-cols-2 gap-2 text-sm sm:grid-cols-3">
        <div>
          <dt className="text-muted-foreground">Dado de Vida</dt>
          <dd>d{classDefinition.hit_die}</dd>
        </div>
        <div>
          <dt className="text-muted-foreground">Habilidade Primária</dt>
          <dd className="uppercase">{classDefinition.primary_ability}</dd>
        </div>
        <div>
          <dt className="text-muted-foreground">Resistências</dt>
          <dd className="uppercase">{classDefinition.saving_throw_proficiencies}</dd>
        </div>
      </dl>

      {classDefinition.levels.length > 0 ? (
        <section>
          <h3 className="font-semibold">Progressão por Nível</h3>
          <ul className="mt-2 space-y-2">
            {[...classDefinition.levels]
              .sort((a, b) => a.level - b.level)
              .map((classLevel) => (
                <li key={classLevel.id} className="rounded-md border border-border p-3 text-sm">
                  <p className="font-medium">
                    Nível {classLevel.level}
                    {classLevel.proficiency_bonus !== null
                      ? ` — bônus de proficiência +${classLevel.proficiency_bonus}`
                      : ""}
                  </p>
                  {classLevel.features.length > 0 ? (
                    <ul className="mt-1 space-y-1">
                      {classLevel.features.map((feature) => (
                        <li key={feature.id}>
                          <span className="font-medium">{feature.feature_name}. </span>
                          {feature.description}
                        </li>
                      ))}
                    </ul>
                  ) : null}
                  {classLevel.spell_slots.length > 0 ? (
                    <p className="mt-1 text-xs text-muted-foreground">
                      Espaços de magia:{" "}
                      {classLevel.spell_slots
                        .map((slot) => `nível ${slot.spell_level}: ${slot.slot_count}`)
                        .join(", ")}
                    </p>
                  ) : null}
                  {classLevel.resources.length > 0 ? (
                    <p className="mt-1 text-xs text-muted-foreground">
                      Recursos:{" "}
                      {classLevel.resources
                        .map((resource) => `${resource.resource_key}: ${resource.value}`)
                        .join(", ")}
                    </p>
                  ) : null}
                </li>
              ))}
          </ul>
        </section>
      ) : null}

      {classDefinition.subclasses.length > 0 ? (
        <section>
          <h3 className="font-semibold">Subclasses</h3>
          <ul className="mt-2 space-y-3">
            {classDefinition.subclasses.map((subclass) => (
              <li key={subclass.id} className="rounded-md border border-border p-3 text-sm">
                <p className="font-medium">{subclass.name}</p>
                {subclass.flavor ? (
                  <p className="italic text-muted-foreground">{subclass.flavor}</p>
                ) : null}
                <p className="mt-1 whitespace-pre-line">{subclass.description}</p>
                {subclass.features.length > 0 ? (
                  <ul className="mt-2 space-y-1">
                    {subclass.features.map((feature) => (
                      <li key={feature.id}>
                        <span className="font-medium">{feature.feature_name}. </span>
                        {feature.description}
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
