import type { Spell } from "@/types/catalog";

const ACTION_TYPE_LABELS: Record<string, string> = {
  attack_roll: "Rolagem de ataque",
  saving_throw: "Resistência",
  cast_only: "Sem rolagem",
};

const TARGET_TYPE_LABELS: Record<string, string> = {
  self: "Próprio conjurador",
  ally: "Aliado",
  enemy: "Inimigo",
  area: "Área",
};

/** Structured detail view for a `Spell` — replaces the generic JSON dump (Fase 11). */
export function SpellDetail({ spell }: { spell: Spell }) {
  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">
        {spell.level === 0 ? "Truque" : `Nível ${spell.level}`} · {spell.school}
        {spell.ritual ? " · Ritual" : ""}
        {spell.concentration ? " · Concentração" : ""}
      </p>

      <dl className="grid grid-cols-2 gap-2 text-sm sm:grid-cols-4">
        <div>
          <dt className="text-muted-foreground">Tempo de Conjuração</dt>
          <dd>{spell.casting_time}</dd>
        </div>
        <div>
          <dt className="text-muted-foreground">Alcance</dt>
          <dd>{spell.range}</dd>
        </div>
        <div>
          <dt className="text-muted-foreground">Duração</dt>
          <dd>{spell.duration}</dd>
        </div>
        <div>
          <dt className="text-muted-foreground">Componentes</dt>
          <dd>{spell.components}</dd>
        </div>
      </dl>

      {spell.action_type || spell.target_type ? (
        <p className="text-sm">
          {spell.action_type ? (
            <span className="font-medium">{ACTION_TYPE_LABELS[spell.action_type] ?? spell.action_type}</span>
          ) : null}
          {spell.action_type && spell.target_type ? " · " : ""}
          {spell.target_type ? TARGET_TYPE_LABELS[spell.target_type] ?? spell.target_type : ""}
        </p>
      ) : null}

      <p className="whitespace-pre-line text-sm">{spell.description}</p>

      {spell.higher_levels ? (
        <p className="text-sm">
          <span className="font-medium">Em níveis superiores: </span>
          {spell.higher_levels}
        </p>
      ) : null}

      {spell.damages.length > 0 ? (
        <section>
          <h3 className="font-semibold">Dano</h3>
          <ul className="mt-1 space-y-1 text-sm">
            {spell.damages.map((damage) => (
              <li key={damage.id} className="font-mono">
                {damage.dice_expression} ({damage.damage_type}) —{" "}
                {damage.scaling_type === "slot_level"
                  ? `espaço de nível ${damage.scaling_key}`
                  : `nível de personagem ${damage.scaling_key}`}
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {spell.classes.length > 0 ? (
        <p className="text-sm">
          <span className="font-medium">Classes: </span>
          {spell.classes.map((spellClass) => spellClass.name).join(", ")}
        </p>
      ) : null}
    </div>
  );
}
