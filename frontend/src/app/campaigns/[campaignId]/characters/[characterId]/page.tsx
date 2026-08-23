"use client";

import { useParams } from "next/navigation";

import { CharacterSheet } from "@/components/characters/character-sheet";
import { useCharacter } from "@/hooks/use-character";

export default function CharacterSheetPage() {
  const { characterId } = useParams<{ campaignId: string; characterId: string }>();
  const { data: character, isLoading } = useCharacter(characterId);

  if (isLoading) {
    return <p className="p-6 text-sm text-muted-foreground">Carregando…</p>;
  }

  if (!character) {
    return <p className="p-6 text-sm text-muted-foreground">Personagem não encontrado.</p>;
  }

  return (
    <main className="mx-auto max-w-3xl px-6 py-10">
      <CharacterSheet character={character} />
    </main>
  );
}
