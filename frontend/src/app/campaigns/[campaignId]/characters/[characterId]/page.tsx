"use client";

import { useParams } from "next/navigation";

import { CharacterSessionsDropdown } from "@/components/characters/character-sessions-dropdown";
import { CharacterSheet } from "@/components/characters/character-sheet";
import { AppNavMenu } from "@/components/layout/app-nav-menu";
import { useMyMembership } from "@/hooks/use-campaign";
import { useCharacter } from "@/hooks/use-character";

export default function CharacterSheetPage() {
  const { campaignId, characterId } = useParams<{
    campaignId: string;
    characterId: string;
  }>();
  const { data: character, isLoading } = useCharacter(characterId);
  const { data: membership } = useMyMembership(campaignId);

  if (isLoading) {
    return <p className="p-6 text-sm text-muted-foreground">Carregando…</p>;
  }

  if (!character) {
    return <p className="p-6 text-sm text-muted-foreground">Personagem não encontrado.</p>;
  }

  return (
    <main className="mx-auto max-w-3xl px-6 py-10">
      <div className="mb-4 flex items-center justify-between gap-2">
        <AppNavMenu campaignId={campaignId} role={membership?.role} />
        <CharacterSessionsDropdown campaignId={campaignId} characterId={characterId} />
      </div>
      <CharacterSheet campaignId={campaignId} character={character} />
    </main>
  );
}
