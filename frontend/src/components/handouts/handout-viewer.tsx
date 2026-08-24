import type { Handout } from "@/types/handout";

/** Renders a handout's content: text inline, image/map as a large image. */
export function HandoutViewer({ handout }: { handout: Handout }) {
  if (handout.handout_type === "text") {
    return <p className="whitespace-pre-wrap text-sm">{handout.content}</p>;
  }

  if (!handout.url) {
    return <p className="text-sm text-muted-foreground">Arquivo não disponível.</p>;
  }

  // Backend-served path (local disk today, S3 later) — not something
  // next/image's static loader config can know about ahead of time.
  // eslint-disable-next-line @next/next/no-img-element
  return <img src={handout.url} alt={handout.title} className="w-full rounded-md" />;
}
