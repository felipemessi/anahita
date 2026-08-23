"use client";

import Link from "next/link";
import { useParams } from "next/navigation";

import { useSessions } from "@/hooks/use-session";
import { useLocations, useLocationSessions } from "@/hooks/use-world";

const LOCATION_TYPE_LABEL: Record<string, string> = {
  city: "Cidade",
  town: "Vila",
  dungeon: "Masmorra",
  wilderness: "Terras selvagens",
  building: "Edificação",
  region: "Região",
  plane: "Plano",
};

export default function LocationDetailPage() {
  const { campaignId, locationId } = useParams<{
    campaignId: string;
    locationId: string;
  }>();
  const { data: locations, isLoading } = useLocations(campaignId);
  const location = locations?.find((candidate) => candidate.id === locationId);
  const parent = locations?.find((candidate) => candidate.id === location?.parent_location_id);
  const children = locations?.filter((candidate) => candidate.parent_location_id === locationId) ?? [];

  const { data: sessionLinks } = useLocationSessions(locationId);
  const { data: campaignSessions } = useSessions(campaignId);
  const sessionsById = new Map(
    (campaignSessions ?? []).map((session) => [session.id, session]),
  );

  if (isLoading) {
    return (
      <main className="mx-auto max-w-3xl px-6 py-10">
        <p className="text-sm text-muted-foreground">Carregando…</p>
      </main>
    );
  }
  if (!location) {
    return (
      <main className="mx-auto max-w-3xl px-6 py-10">
        <p className="text-sm text-muted-foreground">Local não encontrado.</p>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-3xl space-y-6 px-6 py-10">
      <header>
        {parent ? (
          <Link
            href={`/campaigns/${campaignId}/world/locations/${parent.id}`}
            className="text-xs text-muted-foreground hover:underline"
          >
            ← {parent.name}
          </Link>
        ) : null}
        <h1 className="text-2xl font-bold">{location.name}</h1>
        <p className="text-sm text-muted-foreground">
          {LOCATION_TYPE_LABEL[location.location_type] ?? location.location_type}
        </p>
      </header>

      {location.description ? <p className="text-sm">{location.description}</p> : null}

      <section className="space-y-1">
        <h2 className="text-sm font-medium text-muted-foreground">Sublocais</h2>
        {children.length > 0 ? (
          <ul className="text-sm">
            {children.map((child) => (
              <li key={child.id}>
                <Link
                  href={`/campaigns/${campaignId}/world/locations/${child.id}`}
                  className="hover:underline"
                >
                  {child.name}
                </Link>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-muted-foreground">Nenhum.</p>
        )}
      </section>

      <section className="space-y-1">
        <h2 className="text-sm font-medium text-muted-foreground">Sessões</h2>
        {sessionLinks && sessionLinks.length > 0 ? (
          <ul className="text-sm">
            {sessionLinks.map((link) => {
              const session = sessionsById.get(link.session_id);
              return (
                <li key={link.id}>
                  {session ? `Sessão ${session.session_number} — ${session.title}` : "Sessão"}
                  {link.visit_note ? `: ${link.visit_note}` : ""}
                </li>
              );
            })}
          </ul>
        ) : (
          <p className="text-sm text-muted-foreground">Nenhuma.</p>
        )}
      </section>
    </main>
  );
}
