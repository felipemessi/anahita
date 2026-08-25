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
from app.characters.domain import FeatureSourceType, Skill
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
    # Single normalized-copper balance (1 cp = base unit; 1 sp = 10, 1 ep = 50,
    # 1 gp = 100, 1 pp = 1000 — same convention already used for catalog item
    # prices, see `app.catalog.seeds.convert_srd._cost_in_cp`), rather than
    # five separate cp/sp/ep/gp/pp columns: simpler balance math (one
    # integer, one non-negative check) and display can still split it into
    # denominations client-side.
    currency_cp: Mapped[int] = mapped_column(Integer, default=0)
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


class CharacterEquipment(Base):
    """An item a character carries."""

    __tablename__ = "character_equipment"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    character_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("characters.id"))
    item_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("catalog_items.id")
    )
    equipped: Mapped[bool] = mapped_column(Boolean, default=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    attunement: Mapped[bool] = mapped_column(Boolean, default=False)

    character: Mapped[Character] = relationship(back_populates="equipment")
