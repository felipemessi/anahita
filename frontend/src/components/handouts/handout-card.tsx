"use client";

import { useState } from "react";

import { HandoutRevealButton } from "@/components/handouts/handout-reveal-button";
import { HandoutViewer } from "@/components/handouts/handout-viewer";
import type { Handout } from "@/types/handout";

const TYPE_LABEL: Record<Handout["handout_type"], string> = {
  text: "Texto",
  image: "Imagem",
  map: "Mapa",
};

/** Summary card for a handout: title, type, reveal state, and an expandable viewer. */
export function HandoutCard({
  handout,
  campaignId,
  isDm = false,
}: {
  handout: Handout;
  campaignId: string;
  isDm?: boolean;
}) {
  const [open, setOpen] = useState(false);

  return (
    <article className="space-y-2 rounded-lg border border-border bg-card p-4">
      <header className="flex items-center justify-between gap-2">
        <div>
          <p className="font-medium">{handout.title}</p>
          <p className="text-xs text-muted-foreground">
            {TYPE_LABEL[handout.handout_type]}
            {isDm && !handout.is_revealed ? " · não revelado" : ""}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {isDm && !handout.is_revealed ? (
            <HandoutRevealButton handoutId={handout.id} campaignId={campaignId} />
          ) : null}
          <button
            type="button"
            onClick={() => setOpen((visible) => !visible)}
            className="shrink-0 rounded-md border border-border px-3 py-1 text-xs hover:bg-secondary/50"
          >
            {open ? "Ocultar" : "Ver"}
          </button>
        </div>
      </header>

      {open ? <HandoutViewer handout={handout} /> : null}
    </article>
  );
}
