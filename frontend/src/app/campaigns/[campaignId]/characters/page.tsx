"use client";

import Link from "next/link";
import { useParams } from "next/navigation";

import { useCharacters } from "@/hooks/use-character";
import { isFullCharacter } from "@/types/character";

export default function CharactersPage() {
  const { campaignId } = useParams<{ campaignId: string }>();
  const { data: characters, isLoading } = useCharacters(campaignId);

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
          {characters.map((character) => (
            <li key={character.id}>
              <Link
                href={`/campaigns/${campaignId}/characters/${character.id}`}
                className="flex items-center justify-between rounded-lg border border-border bg-card px-4 py-3 transition-colors hover:bg-secondary/40"
              >
                <span>{character.name}</span>
                <span className="font-mono text-sm text-muted-foreground">
                  Nível {character.level}
                  {isFullCharacter(character)
                    ? ` · ${character.hit_point_current}/${character.hit_point_max} PV`
                    : ""}
                </span>
              </Link>
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-sm text-muted-foreground">
          Nenhum personagem nesta campanha ainda.
        </p>
      )}
    </main>
  );
}
