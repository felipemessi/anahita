import type { Rule } from "@/types/catalog";

/** Structured detail view for a `Rule` — replaces the generic JSON dump (Fase 11). */
export function RuleDetail({ rule }: { rule: Rule }) {
  return (
    <div className="space-y-4">
      <p className="whitespace-pre-line text-sm">{rule.desc}</p>

      {rule.sections.length > 0 ? (
        <div className="space-y-3">
          {rule.sections.map((section) => (
            <section key={section.id}>
              <h3 className="font-semibold">{section.name}</h3>
              <p className="mt-1 whitespace-pre-line text-sm">{section.desc}</p>
            </section>
          ))}
        </div>
      ) : null}
    </div>
  );
}
