/** A small "N label" pill — e.g. "3 facções". Renders nothing when count is 0. */
export function EntityLinkBadge({ label, count }: { label: string; count: number }) {
  if (count === 0) return null;
  return (
    <span className="rounded-full border border-border px-2 py-0.5 text-xs text-muted-foreground">
      {count} {label}
    </span>
  );
}
