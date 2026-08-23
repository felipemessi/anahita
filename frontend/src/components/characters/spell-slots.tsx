/**
 * Backend `Character` schema has no spellcasting data yet (no spell slots,
 * prepared spells, etc.) — see anahita-frontend-backlog.md Fase 1. Renders
 * a placeholder until that's modeled server-side.
 */
export function SpellSlots() {
  return (
    <section aria-label="Magias" className="rounded-lg border border-border bg-card p-4">
      <h3 className="font-semibold">Magias</h3>
      <p className="mt-1 text-sm text-muted-foreground">
        Em breve (aguardando modelagem de conjuração no backend).
      </p>
    </section>
  );
}
