"use client";

import { useParams, useRouter } from "next/navigation";
import { useState } from "react";

import { StepAbilityScores } from "@/components/characters/creation-wizard/step-ability-scores";
import { StepBackground } from "@/components/characters/creation-wizard/step-background";
import { StepClass } from "@/components/characters/creation-wizard/step-class";
import { StepEquipment } from "@/components/characters/creation-wizard/step-equipment";
import { StepRace } from "@/components/characters/creation-wizard/step-race";
import { StepReview } from "@/components/characters/creation-wizard/step-review";
import {
  ABILITY_ORDER,
  INITIAL_WIZARD_STATE,
  type WizardState,
} from "@/components/characters/creation-wizard/wizard-state";
import { useMyMembership } from "@/hooks/use-campaign";
import { useCatalogEntry } from "@/hooks/use-catalog";
import { useCreateCharacter } from "@/hooks/use-character";
import { ApiError } from "@/lib/api/client";
import type { CharacterAbilityScoreCreate, CharacterCreate } from "@/types/character";

const STEPS = [
  { key: "race", label: "Raça" },
  { key: "class", label: "Classe" },
  { key: "background", label: "Antecedente" },
  { key: "ability-scores", label: "Atributos" },
  { key: "equipment", label: "Equipamento" },
  { key: "review", label: "Revisão" },
] as const;

export default function CharacterCreationWizardPage() {
  const { campaignId } = useParams<{ campaignId: string }>();
  const router = useRouter();
  const { data: membership } = useMyMembership(campaignId);
  const createCharacter = useCreateCharacter();

  const [step, setStep] = useState(0);
  const [wizardState, setWizardState] = useState<WizardState>(INITIAL_WIZARD_STATE);
  const [error, setError] = useState<string | null>(null);

  const { data: selectedBackground } = useCatalogEntry("backgrounds", wizardState.backgroundId);

  function patch(update: Partial<WizardState>) {
    setWizardState((prev) => ({ ...prev, ...update }));
  }

  async function handleSubmit() {
    if (!membership) return;
    setError(null);

    const abilityScores: CharacterAbilityScoreCreate[] = ABILITY_ORDER.filter(
      (ability) => wizardState.abilityScores[ability] !== null,
    ).map((ability) => ({
      ability,
      base_score: wizardState.abilityScores[ability] as number,
    }));

    const payload: CharacterCreate = {
      campaign_member_id: membership.id,
      name: wizardState.name,
      race_id: wizardState.raceId,
      subrace_id: wizardState.subraceId,
      alignment: wizardState.alignment || null,
      background: selectedBackground?.name ?? null,
      ability_scores: abilityScores,
      classes: [
        {
          class_definition_id: wizardState.classId,
          subclass_id: wizardState.subclassId,
          level: 1,
        },
      ],
    };

    try {
      const character = await createCharacter.mutateAsync(payload);
      router.push(`/campaigns/${campaignId}/characters/${character.id}`);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? "Não foi possível criar o personagem. Verifique os campos."
          : "Erro inesperado ao criar personagem.",
      );
    }
  }

  return (
    <main className="mx-auto max-w-2xl space-y-6 px-6 py-10">
      <div>
        <h1 className="text-2xl font-bold">Criar personagem</h1>
        <p className="text-sm text-muted-foreground">
          Passo {step + 1} de {STEPS.length}: {STEPS[step]?.label}
        </p>
      </div>

      {step === 0 ? (
        <StepRace campaignId={campaignId} value={wizardState} onChange={patch} />
      ) : null}
      {step === 1 ? (
        <StepClass campaignId={campaignId} value={wizardState} onChange={patch} />
      ) : null}
      {step === 2 ? (
        <StepBackground campaignId={campaignId} value={wizardState} onChange={patch} />
      ) : null}
      {step === 3 ? <StepAbilityScores value={wizardState} onChange={patch} /> : null}
      {step === 4 ? <StepEquipment value={wizardState} /> : null}
      {step === 5 ? (
        <StepReview
          value={wizardState}
          isSubmitting={createCharacter.isPending}
          error={error}
          onSubmit={handleSubmit}
        />
      ) : null}

      <div className="flex justify-between">
        <button
          type="button"
          onClick={() => setStep((s) => Math.max(0, s - 1))}
          disabled={step === 0}
          className="rounded-md border border-border px-4 py-2 text-sm disabled:opacity-40"
        >
          Voltar
        </button>
        {step < STEPS.length - 1 ? (
          <button
            type="button"
            onClick={() => setStep((s) => Math.min(STEPS.length - 1, s + 1))}
            className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:opacity-90"
          >
            Próximo
          </button>
        ) : null}
      </div>
    </main>
  );
}
