"use client";

import { useCatalogEntry, useCatalogList } from "@/hooks/use-catalog";
import type { WizardState } from "@/components/characters/creation-wizard/wizard-state";

export function StepRace({
  campaignId,
  value,
  onChange,
}: {
  campaignId: string;
  value: WizardState;
  onChange: (patch: Partial<WizardState>) => void;
}) {
  const { data: races } = useCatalogList("races", { campaign_id: campaignId });
  const { data: race } = useCatalogEntry("races", value.raceId);

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">Raça</h2>

      <label htmlFor="race" className="block text-sm font-medium">
        Escolha a raça
      </label>
      <select
        id="race"
        value={value.raceId}
        onChange={(e) => onChange({ raceId: e.target.value, subraceId: null })}
        className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
      >
        <option value="">Selecione…</option>
        {races?.map((r) => (
          <option key={r.id} value={r.id}>
            {r.name}
          </option>
        ))}
      </select>

      {race && race.subraces.length > 0 ? (
        <>
          <label htmlFor="subrace" className="block text-sm font-medium">
            Subraça
          </label>
          <select
            id="subrace"
            value={value.subraceId ?? ""}
            onChange={(e) => onChange({ subraceId: e.target.value || null })}
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
          >
            <option value="">Nenhuma</option>
            {race.subraces.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
        </>
      ) : null}
    </div>
  );
}
