"use client";

import { useState } from "react";
import { useParams } from "next/navigation";

import { LocationTree } from "@/components/world/location-tree";
import { useMyMembership } from "@/hooks/use-campaign";
import { useSessions } from "@/hooks/use-session";
import {
  useCreateLocation,
  useLinkLocationSession,
  useLocationTree,
  useLocations,
} from "@/hooks/use-world";
import type { LocationType } from "@/types/world";

const LOCATION_TYPES: LocationType[] = [
  "region",
  "city",
  "town",
  "building",
  "dungeon",
  "wilderness",
  "plane",
];

export default function LocationsPage() {
  const { campaignId } = useParams<{ campaignId: string }>();
  const { data: tree, isLoading } = useLocationTree(campaignId);
  const { data: locations } = useLocations(campaignId);
  const { data: membership } = useMyMembership(campaignId);
  const isDm = membership?.role === "dm";

  const [name, setName] = useState("");
  const [locationType, setLocationType] = useState<LocationType>("region");
  const [parentId, setParentId] = useState("");
  const createLocation = useCreateLocation(campaignId);

  const [linkLocationId, setLinkLocationId] = useState("");
  const [linkSessionId, setLinkSessionId] = useState("");
  const { data: campaignSessions } = useSessions(campaignId);
  const linkLocationSession = useLinkLocationSession(linkLocationId);

  function handleCreate(event: React.FormEvent) {
    event.preventDefault();
    if (!name.trim()) return;
    createLocation.mutate(
      {
        name: name.trim(),
        location_type: locationType,
        description: "",
        parent_location_id: parentId || null,
      },
      { onSuccess: () => setName("") },
    );
  }

  function handleLinkSession(event: React.FormEvent) {
    event.preventDefault();
    if (!linkLocationId || !linkSessionId) return;
    linkLocationSession.mutate(
      { session_id: linkSessionId },
      { onSuccess: () => setLinkSessionId("") },
    );
  }

  return (
    <main className="mx-auto max-w-3xl space-y-6 px-6 py-10">
      <h1 className="text-2xl font-bold">Locais</h1>

      {isDm ? (
        <form onSubmit={handleCreate} className="flex flex-wrap gap-2">
          <input
            value={name}
            onChange={(event) => setName(event.target.value)}
            placeholder="Nome"
            className="flex-1 rounded-md border border-border bg-background px-3 py-2 text-sm"
          />
          <select
            value={locationType}
            onChange={(event) => setLocationType(event.target.value as LocationType)}
            className="rounded-md border border-border bg-background px-3 py-2 text-sm"
          >
            {LOCATION_TYPES.map((type) => (
              <option key={type} value={type}>
                {type}
              </option>
            ))}
          </select>
          <select
            value={parentId}
            onChange={(event) => setParentId(event.target.value)}
            className="rounded-md border border-border bg-background px-3 py-2 text-sm"
          >
            <option value="">Sem local pai</option>
            {locations?.map((location) => (
              <option key={location.id} value={location.id}>
                {location.name}
              </option>
            ))}
          </select>
          <button
            type="submit"
            disabled={!name.trim() || createLocation.isPending}
            className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:opacity-90 disabled:opacity-50"
          >
            Criar local
          </button>
        </form>
      ) : null}
      {createLocation.isError ? (
        <p role="alert" className="text-sm text-destructive">
          Não foi possível criar o local.
        </p>
      ) : null}

      {isDm && locations && locations.length > 0 ? (
        <form onSubmit={handleLinkSession} className="flex flex-wrap gap-2">
          <select
            value={linkLocationId}
            onChange={(event) => setLinkLocationId(event.target.value)}
            aria-label="Local a vincular a uma sessão"
            className="flex-1 rounded-md border border-border bg-background px-3 py-2 text-xs"
          >
            <option value="">Vincular local a uma sessão…</option>
            {locations.map((location) => (
              <option key={location.id} value={location.id}>
                {location.name}
              </option>
            ))}
          </select>
          <select
            value={linkSessionId}
            onChange={(event) => setLinkSessionId(event.target.value)}
            aria-label="Sessão visitada"
            className="flex-1 rounded-md border border-border bg-background px-3 py-2 text-xs"
          >
            <option value="">Selecione uma sessão</option>
            {campaignSessions?.map((session) => (
              <option key={session.id} value={session.id}>
                Sessão {session.session_number} — {session.title}
              </option>
            ))}
          </select>
          <button
            type="submit"
            disabled={!linkLocationId || !linkSessionId || linkLocationSession.isPending}
            className="rounded-md border border-border px-3 py-1.5 text-xs hover:bg-secondary/50 disabled:opacity-50"
          >
            Vincular
          </button>
        </form>
      ) : null}

      {isLoading ? (
        <p className="text-sm text-muted-foreground">Carregando…</p>
      ) : (
        <LocationTree tree={tree ?? []} />
      )}
    </main>
  );
}
