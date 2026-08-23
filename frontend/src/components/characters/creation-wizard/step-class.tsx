"use client";

import { useCatalogEntry, useCatalogList } from "@/hooks/use-catalog";
import type { WizardState } from "@/components/characters/creation-wizard/wizard-state";

export function StepClass({
  campaignId,
  value,
  onChange,
}: {
  campaignId: string;
  value: WizardState;
  onChange: (patch: Partial<WizardState>) => void;
}) {
  const { data: classes } = useCatalogList("classes", { campaign_id: campaignId });
  const { data: classDefinition } = useCatalogEntry("classes", value.classId);

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">Classe</h2>

      <label htmlFor="class" className="block text-sm font-medium">
        Escolha a classe
      </label>
      <select
        id="class"
        value={value.classId}
        onChange={(e) => onChange({ classId: e.target.value, subclassId: null })}
        className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
      >
        <option value="">Selecione…</option>
        {classes?.map((c) => (
          <option key={c.id} value={c.id}>
            {c.name}
          </option>
        ))}
      </select>

      {classDefinition && classDefinition.subclasses.length > 0 ? (
        <>
          <label htmlFor="subclass" className="block text-sm font-medium">
            Subclasse
          </label>
          <select
            id="subclass"
            value={value.subclassId ?? ""}
            onChange={(e) => onChange({ subclassId: e.target.value || null })}
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
          >
            <option value="">Nenhuma</option>
            {classDefinition.subclasses.map((s) => (
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
