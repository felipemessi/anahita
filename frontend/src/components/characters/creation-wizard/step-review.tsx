"use client";

import {
  ABILITY_LABELS,
  ABILITY_ORDER,
  type WizardState,
} from "@/components/characters/creation-wizard/wizard-state";

export function StepReview({
  value,
  isSubmitting,
  error,
  onSubmit,
}: {
  value: WizardState;
  isSubmitting: boolean;
  error: string | null;
  onSubmit: () => void;
}) {
  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">Revisão</h2>

      <dl className="space-y-1 text-sm">
        <div className="flex justify-between">
          <dt className="text-muted-foreground">Nome</dt>
          <dd>{value.name || "—"}</dd>
        </div>
        <div className="flex justify-between">
          <dt className="text-muted-foreground">Alinhamento</dt>
          <dd>{value.alignment || "—"}</dd>
        </div>
        {ABILITY_ORDER.map((ability) => (
          <div key={ability} className="flex justify-between">
            <dt className="text-muted-foreground">{ABILITY_LABELS[ability]}</dt>
            <dd>{value.abilityScores[ability] ?? "—"}</dd>
          </div>
        ))}
      </dl>

      {error ? (
        <p role="alert" className="text-sm text-destructive">
          {error}
        </p>
      ) : null}

      <button
        type="button"
        onClick={onSubmit}
        disabled={isSubmitting}
        className="w-full rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-opacity hover:opacity-90 disabled:opacity-60"
      >
        {isSubmitting ? "Criando…" : "Criar personagem"}
      </button>
    </div>
  );
}
