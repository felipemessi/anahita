"""SQLAlchemy models for the characters domain (PRD section 7.3)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.catalog.domain import AbilityScore
from app.characters.domain import AbilityGenerationMethod, FeatureSourceType, Skill
from app.database import Base

# Shared instances so each Postgres enum type is only ever declared once, even
# though it backs columns on more than one table.
_ability_score_enum = SAEnum(AbilityScore, name="characterabilityscoreability")
_skill_enum = SAEnum(Skill, name="characterskill")
_feature_source_type_enum = SAEnum(FeatureSourceType, name="characterfeaturesourcetype")


class Character(Base):
    """A player character sheet, belonging to one campaign membership."""

    __tablename__ = "characters"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    campaign_member_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("campaign_members.id")
    )
    name: Mapped[str] = mapped_column(String(255))
    race_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("catalog_races.id")
    )
    subrace_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("catalog_subraces.id")
    )
    level: Mapped[int] = mapped_column(Integer, default=1)
    experience_points: Mapped[int] = mapped_column(Integer, default=0)
    alignment: Mapped[str | None] = mapped_column(String(100))
    background: Mapped[str | None] = mapped_column(String(255))
    hit_point_max: Mapped[int] = mapped_column(Integer)
    hit_point_current: Mapped[int] = mapped_column(Integer)
    temporary_hit_points: Mapped[int] = mapped_column(Integer, default=0)
    armor_class: Mapped[int] = mapped_column(Integer)
    speed: Mapped[int] = mapped_column(Integer)
    inspiration: Mapped[bool] = mapped_column(Boolean, default=False)
    proficiency_bonus: Mapped[int] = mapped_column(Integer)
    # Death saving throws, tracked only while `hit_point_current == 0`
    # (Fase 7) — reset to 0 whenever the character is healed above 0, or
    # (implicitly, via `is_dead`) once three failures are reached. See
    # `CharacterService.death_save` and `_register_hp_change`.
    death_save_successes: Mapped[int] = mapped_column(Integer, default=0)
    death_save_failures: Mapped[int] = mapped_column(Integer, default=0)
    is_dead: Mapped[bool] = mapped_column(Boolean, default=False)
    # The spell currently being concentrated on, if any — only one at a
    # time (PHB rule), replaced/cleared by `CharacterService.cast_spell`
    # and `CharacterService.set_concentration` (Fase 7).
    concentrating_spell_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("catalog_spells.id")
    )
    # Active duration/expiration for `concentrating_spell_id` (Fase 12) —
    # set together with it by `CharacterService._start_concentration` and
    # cleared together with it wherever concentration ends. Exactly one of
    # the two duration modes below is populated at a time, matching how the
    # spell was cast:
    #
    # - Inside an encounter: `concentration_encounter_id` +
    #   `concentration_round_started` (the encounter's `current_round` at
    #   cast time) + `concentration_duration_rounds` (the spell's duration
    #   converted to whole combat rounds, `engine.spell_duration`) — combat
    #   time, same convention as `EncounterCondition.duration_rounds`.
    #   Remaining rounds are computed on read from the encounter's current
    #   round, never decremented in place.
    # - Outside an encounter: `concentration_expires_at`, a wall-clock
    #   deadline computed from `datetime.now(UTC)` + the spell's duration.
    #
    # All four stay `None` when the spell's duration has nothing to track
    # ("Instantaneous", "Special", "Until dispelled" — see
    # `engine.spell_duration.parse_spell_duration`), meaning concentration
    # only ends explicitly (a saving throw failure, casting another spell,
    # or `set_concentration`), never by a clock.
    concentration_encounter_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("encounters.id")
    )
    concentration_round_started: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    concentration_duration_rounds: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    concentration_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # Single normalized-copper balance (1 cp = base unit; 1 sp = 10, 1 ep = 50,
    # 1 gp = 100, 1 pp = 1000 — same convention already used for catalog item
    # prices, see `app.catalog.seeds.convert_srd._cost_in_cp`), rather than
    # five separate cp/sp/ep/gp/pp columns: simpler balance math (one
    # integer, one non-negative check) and display can still split it into
    # denominations client-side.
    currency_cp: Mapped[int] = mapped_column(Integer, default=0)
    # How the player generated the character's base ability scores — kept
    # for reference only (e.g. so a re-roll UI knows which flow to reopen);
    # nullable so existing characters (created before this field existed)
    # are unaffected.
    generation_method: Mapped[AbilityGenerationMethod | None] = mapped_column(
        SAEnum(AbilityGenerationMethod, name="abilitygenerationmethod")
    )
    # Abstract reference resolved to a URL by `StorageService`, same pattern
    # as `Handout.storage_key` (Fase 10) — the raw portrait image is never
    # stored in the database. `None` when the character has no portrait set.
    portrait_key: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    ability_scores: Mapped[list[CharacterAbilityScore]] = relationship(
        back_populates="character", cascade="all, delete-orphan"
    )
    skills: Mapped[list[CharacterSkill]] = relationship(
        back_populates="character", cascade="all, delete-orphan"
    )
    classes: Mapped[list[CharacterClass]] = relationship(
        back_populates="character", cascade="all, delete-orphan"
    )
    features: Mapped[list[CharacterFeature]] = relationship(
        back_populates="character", cascade="all, delete-orphan"
    )
    feature_choices: Mapped[list[CharacterFeatureChoice]] = relationship(
        back_populates="character", cascade="all, delete-orphan"
    )
    race_choices: Mapped[list[CharacterRaceChoice]] = relationship(
        back_populates="character", cascade="all, delete-orphan"
    )
    spells: Mapped[list[CharacterSpell]] = relationship(
        back_populates="character", cascade="all, delete-orphan"
    )
    spell_slots: Mapped[list[CharacterSpellSlot]] = relationship(
        back_populates="character", cascade="all, delete-orphan"
    )
    equipment: Mapped[list[CharacterEquipment]] = relationship(
        back_populates="character", cascade="all, delete-orphan"
    )
    resources: Mapped[list[CharacterResource]] = relationship(
        back_populates="character", cascade="all, delete-orphan"
    )


class CharacterSessionOrder(Base):
    """A character's personal display-order override for one associated session.

    Purely a per-character UI preference (Fase 10) — never touches
    `Session.session_number`, the shared/official ordering every other
    reader (DM notes, other players' sheets) still uses. Rows only exist
    for sessions a player has explicitly reordered; a session the character
    is associated with (via `app.queries.character_sessions`) but has no
    row here falls back to `session_number` order, appended after any
    explicitly ordered sessions — see
    `CharacterService.get_character_sessions`.
    """

    __tablename__ = "character_session_orders"
    __table_args__ = (
        UniqueConstraint(
            "character_id", "session_id", name="uq_character_session_orders"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    character_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("characters.id"))
    session_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("sessions.id"))
    sort_order: Mapped[int] = mapped_column(Integer)


class CharacterAbilityScore(Base):
    """One of a character's six ability scores."""

    __tablename__ = "character_ability_scores"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    character_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("characters.id"))
    ability: Mapped[AbilityScore] = mapped_column(_ability_score_enum)
    base_score: Mapped[int] = mapped_column(Integer)
    asi_bonus: Mapped[int] = mapped_column(Integer, default=0)
    misc_bonus: Mapped[int] = mapped_column(Integer, default=0)
    save_proficient: Mapped[bool] = mapped_column(Boolean, default=False)

    character: Mapped[Character] = relationship(back_populates="ability_scores")


class CharacterSkill(Base):
    """A character's proficiency/expertise state for one of the 18 skills."""

    __tablename__ = "character_skills"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    character_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("characters.id"))
    skill: Mapped[Skill] = mapped_column(_skill_enum)
    proficient: Mapped[bool] = mapped_column(Boolean, default=False)
    expertise: Mapped[bool] = mapped_column(Boolean, default=False)

    character: Mapped[Character] = relationship(back_populates="skills")


class CharacterClass(Base):
    """One class a character has levels in.

    A separate row per class enables multiclass characters.
    """

    __tablename__ = "character_classes"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    character_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("characters.id"))
    class_definition_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("catalog_class_definitions.id")
    )
    subclass_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("catalog_subclass_definitions.id")
    )
    level: Mapped[int] = mapped_column(Integer, default=1)
    # Hit dice spent for this class specifically, out of a max of `level`
    # (the die type itself comes from the class's own `hit_die` in the
    # catalog) — tracked per class rather than one aggregate character total
    # so a multiclass character's dice of different types are accounted for
    # separately (Fase 7).
    hit_dice_used: Mapped[int] = mapped_column(Integer, default=0)

    character: Mapped[Character] = relationship(back_populates="classes")


class CharacterFeature(Base):
    """A class or feat feature a character has (racial features live on Race)."""

    __tablename__ = "character_features"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    character_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("characters.id"))
    source_type: Mapped[FeatureSourceType] = mapped_column(_feature_source_type_enum)
    source_name: Mapped[str] = mapped_column(String(255))
    feature_name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    level_acquired: Mapped[int] = mapped_column(Integer)

    character: Mapped[Character] = relationship(back_populates="features")


class CharacterFeatureChoice(Base):
    """A named option picked for a class feature that offers a choice.

    `feature_id` is the feature granted at the level that required a pick
    (e.g. "Fighting Style", or "Metamagic" at level 10 for a second round
    of picks), `feature_option_id` the specific option chosen — both point
    at `catalog_features.id`, since an option is just a `Feature` row with
    `parent_feature_id` set (PRD Fase 8; see `CharacterService.level_up`).
    A character can hold more than one row for the same `feature_id`
    (multi-pick features like Eldritch Invocations/Metamagic, Fase 8) —
    unique on the actual `(feature_id, feature_option_id)` pair instead, so
    the same option can't be picked twice for the same feature.
    """

    __tablename__ = "character_feature_choices"
    __table_args__ = (
        UniqueConstraint(
            "character_id",
            "feature_id",
            "feature_option_id",
            name="uq_character_feature_choices",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    character_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("characters.id"))
    feature_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("catalog_features.id")
    )
    feature_option_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("catalog_features.id")
    )

    character: Mapped[Character] = relationship(back_populates="feature_choices")


class CharacterRaceChoice(Base):
    """A choice made for a racial trait with options (e.g. High Elf's bonus cantrip)."""

    __tablename__ = "character_race_choices"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    character_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("characters.id"))
    race_trait_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("catalog_race_traits.id")
    )
    chosen_value: Mapped[str] = mapped_column(String(255))

    character: Mapped[Character] = relationship(back_populates="race_choices")


class CharacterSpell(Base):
    """A spell known/prepared by a character."""

    __tablename__ = "character_spells"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    character_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("characters.id"))
    spell_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("catalog_spells.id")
    )
    prepared: Mapped[bool] = mapped_column(Boolean, default=False)
    source_class: Mapped[str | None] = mapped_column(String(100))

    character: Mapped[Character] = relationship(back_populates="spells")


class CharacterSpellSlot(Base):
    """A character's used spell slots at one spell level (1-9).

    The maximum per level is never persisted here — it's derived on read
    from `ClassLevelSpellSlot`, summed across the character's casting
    classes at their own class level (see
    `CharacterService._max_spell_slots`). A simplification worth flagging:
    this sums each casting class's own slot table independently rather than
    implementing the PHB's combined multiclass-spellcaster slot table, so a
    multiclass character with two casting classes gets more slots than the
    full rule would grant. Single-class casters (the common case) are exact.
    """

    __tablename__ = "character_spell_slots"
    __table_args__ = (
        UniqueConstraint(
            "character_id", "spell_level", name="uq_character_spell_slots"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    character_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("characters.id"))
    spell_level: Mapped[int] = mapped_column(Integer)
    used: Mapped[int] = mapped_column(Integer, default=0)

    character: Mapped[Character] = relationship(back_populates="spell_slots")


class CharacterResource(Base):
    """A class resource a character has spent uses of (rage, ki, ...).

    The maximum per level is never persisted here — it's derived on read
    from `ClassLevelResource`, same "compute on read" pattern as
    `CharacterSpellSlot` (Fase 7). Only `resource_key`s in
    `CharacterService._RESOURCE_RECHARGE` are trackable this way — see its
    docstring for why the rest are catalog-only scaling values.
    """

    __tablename__ = "character_resources"
    __table_args__ = (
        UniqueConstraint("character_id", "resource_key", name="uq_character_resources"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    character_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("characters.id"))
    resource_key: Mapped[str] = mapped_column(String(100))
    used: Mapped[int] = mapped_column(Integer, default=0)
    # Which named option (a catalog `Feature`, e.g. "Channel Divinity:
    # Preserve Life") the most recent use spent, for resources with more
    # than one option (Fase 8) — see
    # `CharacterService._RESOURCE_OPTION_PARENT_FEATURES`. `None` for a
    # resource with no option concept, or before its first recorded use.
    last_feature_option_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("catalog_features.id")
    )

    character: Mapped[Character] = relationship(back_populates="resources")


class CharacterEquipment(Base):
    """An item a character carries.

    `item_id`, `magic_item_id`, and `custom_item_name` are mutually
    exclusive, mirroring `app.inventory.models.LootDrop` — an entry is a
    catalog item, a magic item, or a free-text one, never more than one.
    Manually-added entries (via the character sheet's equipment endpoints)
    are always catalog items; magic/custom entries are created only when
    claiming a loot drop of that kind (`InventoryService.claim_loot_drop`).
    """

    __tablename__ = "character_equipment"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    character_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("characters.id"))
    item_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("catalog_items.id")
    )
    magic_item_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("catalog_magic_items.id")
    )
    custom_item_name: Mapped[str | None] = mapped_column(String(255))
    equipped: Mapped[bool] = mapped_column(Boolean, default=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    attunement: Mapped[bool] = mapped_column(Boolean, default=False)

    character: Mapped[Character] = relationship(back_populates="equipment")
