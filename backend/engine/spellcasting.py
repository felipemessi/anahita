"""Spellcasting rules: known/prepared spell limits (PHB casting rules).

Two casting styles exist among SRD classes (PRD §7.4.4 progression):

- **Known casters** (Bard, Ranger, Sorcerer, Warlock) learn a small, fixed
  number of spells per level and simply have them available — the count is
  read directly off `ClassLevelResource.resource_key == "spells_known"`
  (non-cantrip) and `ClassLevelSpellSlot.spell_level == 0` (cantrips), both
  already stored per `ClassLevel` — there is no formula to compute, only a
  lookup, so this module doesn't re-derive it.
- **Prepared casters** (Cleric, Druid, Paladin, Wizard) can know/access far
  more spells than they can ready at once; the size of the daily prepared
  list is a formula: ability modifier + caster level, minimum one.
"""

#: Classes that learn a fixed number of spells per level and keep them.
KNOWN_CASTER_CLASSES: frozenset[str] = frozenset(
    {"bard", "ranger", "sorcerer", "warlock"}
)

#: Classes that prepare a daily list sized by `prepared_spell_limit` out of a
#: much larger pool (whole class list, or a spellbook for Wizard).
PREPARED_CASTER_CLASSES: frozenset[str] = frozenset(
    {"cleric", "druid", "paladin", "wizard"}
)


def prepared_spell_limit(ability_mod: int, caster_level: int) -> int:
    """PHB prepared-caster formula: ability modifier + caster level, min 1."""
    return max(1, ability_mod + caster_level)
