"use client";

import { useState } from "react";
import Link from "next/link";

import { useCreateWikiPageLink, useDeleteWikiPageLink } from "@/hooks/use-wiki";
import { useFactions, useLocations, useNpcs } from "@/hooks/use-world";
import type { WikiPageLink, WikiPageLinkCreate } from "@/types/wiki";

type LinkTarget = "npc" | "location" | "faction";

const TARGET_LABEL: Record<LinkTarget, string> = {
  npc: "NPC",
  location: "Local",
  faction: "Facção",
};

/** Badges linking a wiki page to its NPCs/locations/factions, each navigating to World. */
export function WikiPageLinks({
  campaignId,
  pageId,
  links,
  isDm,
}: {
  campaignId: string;
  pageId: string;
  links: WikiPageLink[];
  isDm: boolean;
}) {
  const { data: npcs } = useNpcs(campaignId);
  const { data: locations } = useLocations(campaignId);
  const { data: factions } = useFactions(campaignId);
  const deleteLink = useDeleteWikiPageLink(pageId);

  const [target, setTarget] = useState<LinkTarget>("npc");
  const [entityId, setEntityId] = useState("");
  const createLink = useCreateWikiPageLink(pageId);

  const optionsByTarget: Record<LinkTarget, { id: string; name: string }[]> = {
    npc: (npcs ?? []).map((npc) => ({ id: npc.id, name: npc.name })),
    location: (locations ?? []).map((location) => ({
      id: location.id,
      name: location.name,
    })),
    faction: (factions ?? []).map((faction) => ({ id: faction.id, name: faction.name })),
  };

  function badge(link: WikiPageLink): { label: string; name: string; href: string } | null {
    if (link.npc_id) {
      const npc = npcs?.find((candidate) => candidate.id === link.npc_id);
      return {
        label: TARGET_LABEL.npc,
        name: npc?.name ?? link.npc_id,
        href: `/campaigns/${campaignId}/world/npcs/${link.npc_id}`,
      };
    }
    if (link.location_id) {
      const location = locations?.find((candidate) => candidate.id === link.location_id);
      return {
        label: TARGET_LABEL.location,
        name: location?.name ?? link.location_id,
        href: `/campaigns/${campaignId}/world/locations/${link.location_id}`,
      };
    }
    if (link.faction_id) {
      const faction = factions?.find((candidate) => candidate.id === link.faction_id);
      return {
        label: TARGET_LABEL.faction,
        name: faction?.name ?? link.faction_id,
        href: `/campaigns/${campaignId}/world/factions/${link.faction_id}`,
      };
    }
    return null;
  }

  function handleAddLink(event: React.FormEvent) {
    event.preventDefault();
    if (!entityId) return;
    const data: WikiPageLinkCreate =
      target === "npc"
        ? { npc_id: entityId }
        : target === "location"
          ? { location_id: entityId }
          : { faction_id: entityId };
    createLink.mutate(data, { onSuccess: () => setEntityId("") });
  }

  return (
    <section className="space-y-2">
      <h2 className="text-sm font-medium text-muted-foreground">Ligações</h2>
      <div className="flex flex-wrap gap-2">
        {links.map((link) => {
          const info = badge(link);
          if (!info) return null;
          return (
            <span
              key={link.id}
              className="flex items-center gap-1 rounded-full border border-border px-2 py-0.5 text-xs"
            >
              <Link href={info.href} className="hover:underline">
                {info.label}: {info.name}
              </Link>
              {isDm ? (
                <button
                  type="button"
                  onClick={() => deleteLink.mutate(link.id)}
                  aria-label={`Remover ligação com ${info.name}`}
                  className="text-muted-foreground hover:text-destructive"
                >
                  ×
                </button>
              ) : null}
            </span>
          );
        })}
        {links.length === 0 ? (
          <p className="text-sm text-muted-foreground">Nenhuma.</p>
        ) : null}
      </div>

      {isDm ? (
        <form onSubmit={handleAddLink} className="flex flex-wrap gap-2">
          <select
            value={target}
            onChange={(event) => {
              setTarget(event.target.value as LinkTarget);
              setEntityId("");
            }}
            aria-label="Tipo de entidade a linkar"
            className="rounded-md border border-border bg-background px-2 py-1.5 text-xs"
          >
            <option value="npc">NPC</option>
            <option value="location">Local</option>
            <option value="faction">Facção</option>
          </select>
          <select
            value={entityId}
            onChange={(event) => setEntityId(event.target.value)}
            aria-label="Entidade a linkar"
            className="flex-1 rounded-md border border-border bg-background px-2 py-1.5 text-xs"
          >
            <option value="">Selecione…</option>
            {optionsByTarget[target].map((option) => (
              <option key={option.id} value={option.id}>
                {option.name}
              </option>
            ))}
          </select>
          <button
            type="submit"
            disabled={!entityId || createLink.isPending}
            className="rounded-md border border-border px-3 py-1 text-xs hover:bg-secondary/50 disabled:opacity-50"
          >
            Linkar
          </button>
        </form>
      ) : null}
    </section>
  );
}
