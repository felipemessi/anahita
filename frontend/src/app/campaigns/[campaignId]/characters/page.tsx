"use client";

import { useEffect } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";

import { useMyMembership } from "@/hooks/use-campaign";
import { useCatalogList } from "@/hooks/use-catalog";
import { useCharacters } from "@/hooks/use-character";
import { isFullCharacter } from "@/types/character";

/**
 * A player only sees a summary (name/race/class(es)/level) for other
 * players' characters — the backend already withholds the rest — and never
 * gets a link to their full sheet, which the direct route would 403/return
 * a summary for anyway. The DM sees every character's full card. A player
 * with exactly one character in the campaign skips the list entirely and
 * is redirected straight to that character's sheet.
 */
export default function CharactersPage() {
  const { campaignId } = useParams<{ campaignId: string }>();
  const router = useRouter();
  const { data: characters, isLoading } = useCharacters(campaignId);
  const { data: membership } = useMyMembership(campaignId);
  const { data: races } = useCatalogList("races", { campaign_id: campaignId });
  const { data: classes } = useCatalogList("classes", { campaign_id: campaignId });
  const isDm = membership?.role === "dm";

  const ownCharacters = characters?.filter(
    (c) => c.campaign_member_id === membership?.id,
  );
  const soleOwnCharacterId =
    !isDm && ownCharacters?.length === 1 ? ownCharacters[0]?.id : undefined;

  useEffect(() => {
    if (soleOwnCharacterId) {
      router.replace(`/campaigns/${campaignId}/characters/${soleOwnCharacterId}`);
    }
  }, [campaignId, router, soleOwnCharacterId]);

  function raceName(raceId: string): string {
    return races?.find((r) => r.id === raceId)?.name ?? raceId;
  }
  function classNames(classDefinitionIds: string[]): string {
    return classDefinitionIds
      .map((id) => classes?.find((c) => c.id === id)?.name ?? id)
      .join(" / ");
  }

  if (soleOwnCharacterId) {
    return (
      <main className="mx-auto max-w-3xl px-6 py-10">
        <p className="text-sm text-muted-foreground">Abrindo sua ficha…</p>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-3xl space-y-6 px-6 py-10">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Personagens</h1>
        <Link
          href={`/campaigns/${campaignId}/characters/new`}
          className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:opacity-90"
        >
          Criar personagem
        </Link>
      </div>

      {isLoading ? (
        <p className="text-sm text-muted-foreground">Carregando…</p>
      ) : characters && characters.length > 0 ? (
        <ul className="space-y-2">
          {characters.map((character) => {
            const isOwnOrDm = isDm || character.campaign_member_id === membership?.id;
            const summary = (
              <>
                <span>{character.name}</span>
                <span className="font-mono text-sm text-muted-foreground">
                  {raceName(character.race_id)} ·{" "}
                  {classNames(character.classes.map((c) => c.class_definition_id))} ·
                  Nível {character.level}
                  {isFullCharacter(character)
                    ? ` · ${character.hit_point_current}/${character.hit_point_max} PV`
                    : ""}
                </span>
              </>
            );

            return (
              <li key={character.id}>
                {isOwnOrDm ? (
                  <Link
                    href={`/campaigns/${campaignId}/characters/${character.id}`}
                    className="flex items-center justify-between rounded-lg border border-border bg-card px-4 py-3 transition-colors hover:bg-secondary/40"
                  >
                    {summary}
                  </Link>
                ) : (
                  <div className="flex items-center justify-between rounded-lg border border-border bg-card px-4 py-3 opacity-80">
                    {summary}
                  </div>
                )}
              </li>
            );
          })}
        </ul>
      ) : (
        <p className="text-sm text-muted-foreground">
          Nenhum personagem nesta campanha ainda.
        </p>
      )}
    </main>
  );
}
