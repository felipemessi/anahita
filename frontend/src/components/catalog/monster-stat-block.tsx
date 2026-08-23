import type { Monster, MonsterAction } from "@/types/catalog";

/**
 * Renders a full `Monster` stat block. Reused by the catalog "monsters"
 * detail screen, World (NPCs with `stat_block_id`) and the Combat tracker
 * (PRD §6.1a, §9.4).
 */
export function MonsterStatBlock({ monster }: { monster: Monster }) {
  const abilityScores: Array<[label: string, value: number]> = [
    ["STR", monster.strength],
    ["DEX", monster.dexterity],
    ["CON", monster.constitution],
    ["INT", monster.intelligence],
    ["WIS", monster.wisdom],
    ["CHA", monster.charisma],
  ];

  return (
    <article className="space-y-4 rounded-lg border border-border bg-card p-4">
      <header>
        <h2 className="text-xl font-bold">{monster.name}</h2>
        <p className="text-sm italic text-muted-foreground">
          {monster.size} {monster.creature_type}
          {monster.creature_subtype ? ` (${monster.creature_subtype})` : ""},{" "}
          {monster.alignment}
        </p>
      </header>

      <dl className="grid grid-cols-2 gap-2 font-mono text-sm sm:grid-cols-4">
        <div>
          <dt className="text-muted-foreground">AC</dt>
          <dd>
            {monster.armor_classes.map((ac) => ac.value).join(" / ") || "—"}
          </dd>
        </div>
        <div>
          <dt className="text-muted-foreground">HP</dt>
          <dd>
            {monster.hit_points} ({monster.hit_dice})
          </dd>
        </div>
        <div>
          <dt className="text-muted-foreground">CR</dt>
          <dd>
            {monster.challenge_rating} ({monster.xp} XP)
          </dd>
        </div>
        <div>
          <dt className="text-muted-foreground">Prof.</dt>
          <dd>{monster.proficiency_bonus ?? "—"}</dd>
        </div>
      </dl>

      <dl className="grid grid-cols-3 gap-2 text-center font-mono text-sm sm:grid-cols-6">
        {abilityScores.map(([label, value]) => (
          <div key={label} className="rounded-md border border-border py-1">
            <dt className="text-xs text-muted-foreground">{label}</dt>
            <dd>{value}</dd>
          </div>
        ))}
      </dl>

      {monster.speed ? (
        <p className="text-sm">
          <span className="font-medium">Deslocamento: </span>
          {[
            monster.speed.walk ? `andando ${monster.speed.walk}` : null,
            monster.speed.fly ? `voando ${monster.speed.fly}` : null,
            monster.speed.swim ? `nadando ${monster.speed.swim}` : null,
            monster.speed.climb ? `escalando ${monster.speed.climb}` : null,
            monster.speed.burrow ? `escavando ${monster.speed.burrow}` : null,
          ]
            .filter(Boolean)
            .join(", ")}
        </p>
      ) : null}

      {monster.senses ? (
        <p className="text-sm">
          <span className="font-medium">Sentidos: </span>
          percepção passiva {monster.senses.passive_perception}
          {monster.senses.darkvision ? `, visão no escuro ${monster.senses.darkvision}` : ""}
        </p>
      ) : null}

      {monster.languages ? (
        <p className="text-sm">
          <span className="font-medium">Idiomas: </span>
          {monster.languages}
        </p>
      ) : null}

      <p className="whitespace-pre-line text-sm">{monster.description}</p>

      <ActionSection title="Ações" actions={monster.actions} />
      <ActionSection title="Ações Lendárias" actions={monster.legendary_actions} />
      <ActionSection title="Reações" actions={monster.reactions} />
      <ActionSection title="Habilidades Especiais" actions={monster.special_abilities} />
    </article>
  );
}

function ActionSection({ title, actions }: { title: string; actions: MonsterAction[] }) {
  if (actions.length === 0) return null;

  return (
    <section>
      <h3 className="font-semibold">{title}</h3>
      <ul className="mt-1 space-y-2">
        {actions.map((action) => (
          <li key={action.id} className="text-sm">
            <span className="font-medium">{action.name}.</span>{" "}
            {action.description}
          </li>
        ))}
      </ul>
    </section>
  );
}
