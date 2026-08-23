"use client";

import { useCatalogEntry } from "@/hooks/use-catalog";
import type { WizardState } from "@/components/characters/creation-wizard/wizard-state";

/**
 * Informational only: `CharacterCreate` has no equipment field on the
 * backend yet, so starting equipment isn't submitted — this just shows what
 * the chosen background grants, for the player's reference.
 */
export function StepEquipment({ value }: { value: WizardState }) {
  const { data: background } = useCatalogEntry("backgrounds", value.backgroundId);

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">Equipamento inicial</h2>
      <p className="text-sm text-muted-foreground">
        Referência do antecedente escolhido — ainda não enviado à API (backend
        não modela equipamento inicial no personagem).
      </p>

      {background && background.equipment.length > 0 ? (
        <ul className="list-inside list-disc text-sm">
          {background.equipment.map((item) => (
            <li key={item.id}>
              {item.item_name}
              {item.quantity > 1 ? ` (x${item.quantity})` : ""}
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-sm text-muted-foreground">
          Nenhum equipamento inicial listado para este antecedente.
        </p>
      )}
    </div>
  );
}
