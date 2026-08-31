import type { Feat } from "@/types/catalog";

/** Structured detail view for a `Feat` — replaces the generic JSON dump (Fase 11). */
export function FeatDetail({ feat }: { feat: Feat }) {
  return (
    <div className="space-y-4">
      <p className="whitespace-pre-line text-sm">{feat.description}</p>

      {feat.prerequisites.length > 0 ? (
        <section>
          <h3 className="font-semibold">Pré-requisitos</h3>
          <ul className="mt-1 space-y-1 text-sm">
            {feat.prerequisites.map((prerequisite) => (
              <li key={prerequisite.id}>Atributo mínimo: {prerequisite.minimum_score}</li>
            ))}
          </ul>
        </section>
      ) : null}
    </div>
  );
}
