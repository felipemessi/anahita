/**
 * Pure display component for a character's portrait — circular
 * (`border-radius: 50%`), falling back to a two-letter initials placeholder
 * when `portraitUrl` is `null`/`undefined` (PRD frontend backlog Fase 10).
 *
 * Deliberately has no upload/remove behavior so it can be reused as-is for
 * map tokens later (Fase 15) — see `CharacterPortrait` for the editable
 * version used in the character sheet header.
 */
export function CharacterAvatar({
  name,
  portraitUrl,
  size = 64,
}: {
  name: string;
  portraitUrl?: string | null;
  size?: number;
}) {
  const initials = getInitials(name);

  if (portraitUrl) {
    // Backend-served path (local disk today, S3 later) — not something
    // next/image's static loader config can know about ahead of time, same
    // as HandoutViewer's image render.
    return (
      // eslint-disable-next-line @next/next/no-img-element
      <img
        src={portraitUrl}
        alt={`Retrato de ${name}`}
        width={size}
        height={size}
        style={{ width: size, height: size, borderRadius: "50%" }}
        className="object-cover"
      />
    );
  }

  return (
    <div
      role="img"
      aria-label={`Retrato de ${name} (sem imagem)`}
      style={{ width: size, height: size, borderRadius: "50%" }}
      className="flex items-center justify-center bg-muted text-sm font-medium text-muted-foreground"
    >
      {initials}
    </div>
  );
}

function getInitials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "?";
  if (parts.length === 1) return parts[0]!.slice(0, 2).toUpperCase();
  return `${parts[0]![0]}${parts[parts.length - 1]![0]}`.toUpperCase();
}
