import type { CharacterSpellSlot } from "@/types/character";

/**
 * Visual indicator of spell slots per circle (filled/empty dots reflecting
 * `used`/`max`) — the actual spending happens from the "conjurar" button on
 * each spell in `spell-list-by-circle.tsx`; this is read-only.
 */
export function SpellSlots({ slots }: { slots: CharacterSpellSlot[] }) {
  if (slots.length === 0) return null;

  return (
    <section aria-label="Slots de magia" className="rounded-lg border border-border bg-card p-4">
      <h2 className="font-semibold">Slots de magia</h2>
      <ul className="mt-2 space-y-1">
        {slots.map((slot) => (
          <li key={slot.spell_level} className="flex items-center gap-2 text-sm">
            <span className="w-20 text-xs text-muted-foreground">
              {slot.spell_level}º círculo
            </span>
            <span
              aria-label={`${slot.max - slot.used} de ${slot.max} slots disponíveis`}
              className="font-mono tracking-widest"
            >
              {Array.from({ length: slot.max }, (_, i) => (i < slot.max - slot.used ? "●" : "○")).join(
                " ",
              )}
            </span>
            <span className="text-xs text-muted-foreground">
              {slot.max - slot.used}/{slot.max}
            </span>
          </li>
        ))}
      </ul>
    </section>
  );
}
