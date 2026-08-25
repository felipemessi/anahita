/**
 * Passive Perception/Investigation/Insight — `10 + bonus`, computed by the
 * backend and returned on `Character`, never calculated client-side.
 */
export function PassiveScores({
  passivePerception,
  passiveInvestigation,
  passiveInsight,
}: {
  passivePerception: number;
  passiveInvestigation: number;
  passiveInsight: number;
}) {
  const scores: Array<[label: string, value: number]> = [
    ["Percepção passiva", passivePerception],
    ["Investigação passiva", passiveInvestigation],
    ["Intuição passiva", passiveInsight],
  ];

  return (
    <section
      aria-label="Perícias passivas"
      className="rounded-lg border border-border bg-card p-4"
    >
      <h2 className="font-semibold">Perícias passivas</h2>
      <dl className="mt-2 grid grid-cols-3 gap-2 text-center">
        {scores.map(([label, value]) => (
          <div key={label}>
            <dt className="text-xs text-muted-foreground">{label}</dt>
            <dd className="font-mono text-lg">{value}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}
