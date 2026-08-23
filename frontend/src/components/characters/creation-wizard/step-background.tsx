"use client";

import { useCatalogList } from "@/hooks/use-catalog";
import type { WizardState } from "@/components/characters/creation-wizard/wizard-state";

/**
 * `CharacterCreate.background` is a free-text field on the backend (not an
 * id reference) — the catalog dropdown here only picks a `backgroundId` to
 * look up its starting equipment for `step-equipment.tsx`. On submit the
 * selected background's name is what actually goes in the payload.
 */
export function StepBackground({
  campaignId,
  value,
  onChange,
}: {
  campaignId: string;
  value: WizardState;
  onChange: (patch: Partial<WizardState>) => void;
}) {
  const { data: backgrounds } = useCatalogList("backgrounds", {
    campaign_id: campaignId,
  });

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">Antecedente</h2>

      <label htmlFor="character-name" className="block text-sm font-medium">
        Nome do personagem
      </label>
      <input
        id="character-name"
        value={value.name}
        onChange={(e) => onChange({ name: e.target.value })}
        className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
      />

      <label htmlFor="background" className="block text-sm font-medium">
        Antecedente
      </label>
      <select
        id="background"
        value={value.backgroundId}
        onChange={(e) => onChange({ backgroundId: e.target.value })}
        className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
      >
        <option value="">Selecione…</option>
        {backgrounds?.map((b) => (
          <option key={b.id} value={b.id}>
            {b.name}
          </option>
        ))}
      </select>

      <label htmlFor="alignment" className="block text-sm font-medium">
        Alinhamento
      </label>
      <input
        id="alignment"
        value={value.alignment}
        onChange={(e) => onChange({ alignment: e.target.value })}
        placeholder="ex.: Neutro e Bom"
        className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
      />
    </div>
  );
}
