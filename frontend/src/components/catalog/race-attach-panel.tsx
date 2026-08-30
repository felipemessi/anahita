"use client";

import { useState, type FormEvent } from "react";

import {
  useAddRaceAbilityBonus,
  useAddRaceSubrace,
  useAddRaceTrait,
  useCatalogEntry,
} from "@/hooks/use-catalog";
import { ApiError } from "@/lib/api/client";
import type { AbilityScore, Race } from "@/types/catalog";

const ABILITIES: readonly AbilityScore[] = ["str", "dex", "con", "int", "wis", "cha"];

function errorMessage(err: unknown): string {
  if (err instanceof ApiError) {
    if (Array.isArray(err.detail)) {
      const messages = err.detail
        .map((item) =>
          item && typeof item === "object" && "msg" in item ? String(item.msg) : null,
        )
        .filter((msg): msg is string => msg !== null);
      if (messages.length > 0) return messages.join(" ");
    }
    return err.message;
  }
  return "Não foi possível salvar. Tente novamente.";
}

/** Attach-an-ability-bonus mini-form, reused standalone here for a homebrew race. */
function AbilityBonusForm({ raceId }: { raceId: string }) {
  const [ability, setAbility] = useState<AbilityScore>("str");
  const [bonus, setBonus] = useState("1");
  const [error, setError] = useState<string | null>(null);
  const addBonus = useAddRaceAbilityBonus(raceId);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    try {
      await addBonus.mutateAsync({ ability, bonus: Number(bonus) });
      setBonus("1");
    } catch (err) {
      setError(errorMessage(err));
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-wrap items-end gap-2">
      <div className="space-y-1">
        <label htmlFor="race-bonus-ability" className="text-xs font-medium">
          Habilidade
        </label>
        <select
          id="race-bonus-ability"
          value={ability}
          onChange={(e) => setAbility(e.target.value as AbilityScore)}
          className="rounded-md border border-input bg-background px-2 py-1 text-sm"
        >
          {ABILITIES.map((a) => (
            <option key={a} value={a}>
              {a}
            </option>
          ))}
        </select>
      </div>
      <div className="space-y-1">
        <label htmlFor="race-bonus-value" className="text-xs font-medium">
          Bônus
        </label>
        <input
          id="race-bonus-value"
          type="number"
          min={-4}
          max={4}
          value={bonus}
          onChange={(e) => setBonus(e.target.value)}
          className="w-20 rounded-md border border-input bg-background px-2 py-1 text-sm"
        />
      </div>
      <button
        type="submit"
        disabled={addBonus.isPending}
        className="rounded-md bg-secondary px-3 py-1.5 text-sm font-medium disabled:opacity-60"
      >
        {addBonus.isPending ? "Adicionando…" : "Adicionar bônus"}
      </button>
      {error ? (
        <p role="alert" className="w-full text-sm text-destructive">
          {error}
        </p>
      ) : null}
    </form>
  );
}

/** Attach-a-trait mini-form, reused standalone here for a homebrew race. */
function TraitForm({ raceId }: { raceId: string }) {
  const [traitName, setTraitName] = useState("");
  const [description, setDescription] = useState("");
  const [mechanicalEffect, setMechanicalEffect] = useState("");
  const [error, setError] = useState<string | null>(null);
  const addTrait = useAddRaceTrait(raceId);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    try {
      await addTrait.mutateAsync({
        trait_name: traitName,
        description,
        mechanical_effect: mechanicalEffect || null,
      });
      setTraitName("");
      setDescription("");
      setMechanicalEffect("");
    } catch (err) {
      setError(errorMessage(err));
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-2">
      <div className="space-y-1">
        <label htmlFor="race-trait-name" className="text-xs font-medium">
          Nome do traço
        </label>
        <input
          id="race-trait-name"
          type="text"
          required
          value={traitName}
          onChange={(e) => setTraitName(e.target.value)}
          className="w-full rounded-md border border-input bg-background px-2 py-1 text-sm"
        />
      </div>
      <div className="space-y-1">
        <label htmlFor="race-trait-description" className="text-xs font-medium">
          Descrição
        </label>
        <textarea
          id="race-trait-description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={2}
          className="w-full rounded-md border border-input bg-background px-2 py-1 text-sm"
        />
      </div>
      <div className="space-y-1">
        <label htmlFor="race-trait-mechanical-effect" className="text-xs font-medium">
          Efeito mecânico
        </label>
        <input
          id="race-trait-mechanical-effect"
          type="text"
          value={mechanicalEffect}
          onChange={(e) => setMechanicalEffect(e.target.value)}
          className="w-full rounded-md border border-input bg-background px-2 py-1 text-sm"
        />
      </div>
      <button
        type="submit"
        disabled={addTrait.isPending}
        className="rounded-md bg-secondary px-3 py-1.5 text-sm font-medium disabled:opacity-60"
      >
        {addTrait.isPending ? "Adicionando…" : "Adicionar traço"}
      </button>
      {error ? (
        <p role="alert" className="text-sm text-destructive">
          {error}
        </p>
      ) : null}
    </form>
  );
}

/**
 * Attach-a-subrace mini-form. A subrace carries its own single ability bonus
 * and trait inline in this UI (the backend accepts a list of each — a DM who
 * needs more than one attaches the subrace first, then repeats via the
 * standalone ability-bonus/trait forms scoped to the parent race... but
 * those only attach to the *race*, not the subrace, so for now a subrace's
 * own extra bonuses/traits beyond the first are a known limitation — see
 * backlog notes).
 */
function SubraceForm({ raceId }: { raceId: string }) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [ability, setAbility] = useState<AbilityScore>("str");
  const [bonus, setBonus] = useState("");
  const [traitName, setTraitName] = useState("");
  const [traitDescription, setTraitDescription] = useState("");
  const [error, setError] = useState<string | null>(null);
  const addSubrace = useAddRaceSubrace(raceId);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    try {
      await addSubrace.mutateAsync({
        name,
        description,
        ability_bonuses: bonus ? [{ ability, bonus: Number(bonus) }] : [],
        traits: traitName
          ? [{ trait_name: traitName, description: traitDescription, mechanical_effect: null }]
          : [],
      });
      setName("");
      setDescription("");
      setBonus("");
      setTraitName("");
      setTraitDescription("");
    } catch (err) {
      setError(errorMessage(err));
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-2">
      <div className="space-y-1">
        <label htmlFor="race-subrace-name" className="text-xs font-medium">
          Nome da sub-raça
        </label>
        <input
          id="race-subrace-name"
          type="text"
          required
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="w-full rounded-md border border-input bg-background px-2 py-1 text-sm"
        />
      </div>
      <div className="space-y-1">
        <label htmlFor="race-subrace-description" className="text-xs font-medium">
          Descrição
        </label>
        <textarea
          id="race-subrace-description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={2}
          className="w-full rounded-md border border-input bg-background px-2 py-1 text-sm"
        />
      </div>
      <div className="flex flex-wrap items-end gap-2">
        <div className="space-y-1">
          <label htmlFor="race-subrace-ability" className="text-xs font-medium">
            Habilidade (opcional)
          </label>
          <select
            id="race-subrace-ability"
            value={ability}
            onChange={(e) => setAbility(e.target.value as AbilityScore)}
            className="rounded-md border border-input bg-background px-2 py-1 text-sm"
          >
            {ABILITIES.map((a) => (
              <option key={a} value={a}>
                {a}
              </option>
            ))}
          </select>
        </div>
        <div className="space-y-1">
          <label htmlFor="race-subrace-bonus" className="text-xs font-medium">
            Bônus
          </label>
          <input
            id="race-subrace-bonus"
            type="number"
            min={-4}
            max={4}
            value={bonus}
            onChange={(e) => setBonus(e.target.value)}
            className="w-20 rounded-md border border-input bg-background px-2 py-1 text-sm"
          />
        </div>
      </div>
      <div className="space-y-1">
        <label htmlFor="race-subrace-trait-name" className="text-xs font-medium">
          Traço da sub-raça (opcional)
        </label>
        <input
          id="race-subrace-trait-name"
          type="text"
          value={traitName}
          onChange={(e) => setTraitName(e.target.value)}
          className="w-full rounded-md border border-input bg-background px-2 py-1 text-sm"
        />
      </div>
      {traitName ? (
        <div className="space-y-1">
          <label htmlFor="race-subrace-trait-description" className="text-xs font-medium">
            Descrição do traço
          </label>
          <textarea
            id="race-subrace-trait-description"
            value={traitDescription}
            onChange={(e) => setTraitDescription(e.target.value)}
            rows={2}
            className="w-full rounded-md border border-input bg-background px-2 py-1 text-sm"
          />
        </div>
      ) : null}
      <button
        type="submit"
        disabled={addSubrace.isPending}
        className="rounded-md bg-secondary px-3 py-1.5 text-sm font-medium disabled:opacity-60"
      >
        {addSubrace.isPending ? "Adicionando…" : "Adicionar sub-raça"}
      </button>
      {error ? (
        <p role="alert" className="text-sm text-destructive">
          {error}
        </p>
      ) : null}
    </form>
  );
}

/**
 * Post-creation attachment panel for a homebrew race (Fase 11): the race
 * itself already exists (created via `RaceHomebrewForm`), this lets the DM
 * attach ability bonuses, traits, and subraces via their dedicated
 * `POST /catalog/races/{id}/...` endpoints, and shows what's been saved so
 * far by re-reading the race back (`useCatalogEntry`).
 */
export function RaceAttachPanel({ race }: { race: Race }) {
  const raceQuery = useCatalogEntry("races", race.id);
  const current = raceQuery.data ?? race;

  return (
    <div className="space-y-6">
      <div className="rounded-md border border-border bg-muted/30 p-3 text-sm">
        <p className="font-medium">
          Raça &quot;{current.name}&quot; criada. Adicione bônus de atributo, traços e
          sub-raças abaixo.
        </p>
      </div>

      <section className="space-y-2">
        <h3 className="text-sm font-semibold">Bônus de atributo</h3>
        <AbilityBonusForm raceId={race.id} />
        <ul className="text-sm text-muted-foreground">
          {current.ability_bonuses.map((b) => (
            <li key={b.id}>
              +{b.bonus} {b.ability}
            </li>
          ))}
        </ul>
      </section>

      <section className="space-y-2">
        <h3 className="text-sm font-semibold">Traços</h3>
        <TraitForm raceId={race.id} />
        <ul className="text-sm text-muted-foreground">
          {current.traits.map((t) => (
            <li key={t.id}>{t.trait_name}</li>
          ))}
        </ul>
      </section>

      <section className="space-y-2">
        <h3 className="text-sm font-semibold">Sub-raças</h3>
        <SubraceForm raceId={race.id} />
        <ul className="text-sm text-muted-foreground">
          {current.subraces.map((s) => (
            <li key={s.id}>{s.name}</li>
          ))}
        </ul>
      </section>
    </div>
  );
}
