"use client";

import { useRef, useState } from "react";

import { CharacterAvatar } from "@/components/characters/character-avatar";
import { useRemoveCharacterPortrait, useUploadCharacterPortrait } from "@/hooks/use-character";
import { ApiError } from "@/lib/api/client";
import type { Character } from "@/types/character";

/**
 * Editable portrait for the character sheet header (PRD frontend backlog
 * Fase 10): the circular `CharacterAvatar`, plus upload/remove controls.
 * Owner-only server-side (backend/app/characters/router.py) — errors from a
 * non-owner viewer surface the same way as `CharacterInfoEditor`'s.
 */
export function CharacterPortrait({ character }: { character: Character }) {
  const uploadPortrait = useUploadCharacterPortrait(character.id);
  const removePortrait = useRemoveCharacterPortrait(character.id);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [error, setError] = useState<string | null>(null);

  const isPending = uploadPortrait.isPending || removePortrait.isPending;

  async function handleFileChange(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    setError(null);
    try {
      await uploadPortrait.mutateAsync(file);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Não foi possível enviar a imagem.");
    } finally {
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  async function handleRemove() {
    setError(null);
    try {
      await removePortrait.mutateAsync();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Não foi possível remover a imagem.");
    }
  }

  return (
    <div className="flex items-center gap-3">
      <CharacterAvatar name={character.name} portraitUrl={character.portrait_url} size={64} />
      <div className="flex flex-col items-start gap-1">
        <label className="cursor-pointer text-sm text-muted-foreground underline hover:text-foreground">
          {character.portrait_url ? "Trocar imagem" : "Adicionar imagem"}
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            aria-label="Imagem do personagem"
            disabled={isPending}
            onChange={handleFileChange}
            className="sr-only"
          />
        </label>
        {character.portrait_url ? (
          <button
            type="button"
            onClick={handleRemove}
            disabled={isPending}
            className="text-sm text-muted-foreground underline hover:text-foreground disabled:opacity-40"
          >
            Remover imagem
          </button>
        ) : null}
        {error ? (
          <p role="alert" className="text-sm text-destructive">
            {error}
          </p>
        ) : null}
      </div>
    </div>
  );
}
