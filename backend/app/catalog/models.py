"""SQLAlchemy models for the catalog domain (D&D 5e SRD reference data)."""

import uuid
from typing import ClassVar

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.catalog.domain import CreatureSize, LanguageType, ProficiencyType
from app.catalog.mixins import CatalogEntityMixin, CatalogI18nMixin
from app.database import Base

#: Reused by every catalog table that carries `is_custom`/`campaign_id` but
#: predates `CatalogEntityMixin` (Race, ClassDefinition, SubclassDefinition) —
#: see `app.catalog.mixins.CatalogEntityMixin` for the canonical version.
_CUSTOM_CAMPAIGN_SCOPE_SQL = (
    "(NOT is_custom AND campaign_id IS NULL) OR (is_custom AND campaign_id IS NOT NULL)"
)


class Race(Base):
    """A playable race from the SRD or a campaign homebrew."""

    __tablename__ = "catalog_races"
    __table_args__ = (
        CheckConstraint(
            _CUSTOM_CAMPAIGN_SCOPE_SQL, name="ck_catalog_races_custom_campaign_scope"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    speed: Mapped[int] = mapped_column(Integer, nullable=False)
    size: Mapped[str] = mapped_column(
        String(20), nullable=False, default=CreatureSize.medium.value
    )
    darkvision_range: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    is_custom: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # FK to campaigns.id — enforced at DB level in migration, omitted here to avoid
    # cross-domain metadata coupling in tests (campaigns domain not yet implemented).
    campaign_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    traits: Mapped[list[RaceTrait]] = relationship(
        "RaceTrait", back_populates="race", cascade="all, delete-orphan"
    )
    subraces: Mapped[list[Subrace]] = relationship(
        "Subrace", back_populates="race", cascade="all, delete-orphan"
    )
    ability_bonuses: Mapped[list[RaceAbilityBonus]] = relationship(
        "RaceAbilityBonus",
        primaryjoin="RaceAbilityBonus.race_id == Race.id",
        back_populates="race",
        cascade="all, delete-orphan",
    )


class RaceTrait(Base):
    """A racial trait associated with a Race."""

    __tablename__ = "catalog_race_traits"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    race_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_races.id", ondelete="CASCADE"),
        nullable=False,
    )
    trait_name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    mechanical_effect: Mapped[str | None] = mapped_column(String(500), nullable=True)

    race: Mapped[Race] = relationship("Race", back_populates="traits")


class Subrace(Base):
    """A subrace variant of a Race."""

    __tablename__ = "catalog_subraces"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    race_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_races.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")

    race: Mapped[Race] = relationship("Race", back_populates="subraces")
    traits: Mapped[list[SubraceTrait]] = relationship(
        "SubraceTrait", back_populates="subrace", cascade="all, delete-orphan"
    )
    ability_bonuses: Mapped[list[RaceAbilityBonus]] = relationship(
        "RaceAbilityBonus",
        primaryjoin="RaceAbilityBonus.subrace_id == Subrace.id",
        back_populates="subrace",
        cascade="all, delete-orphan",
    )


class SubraceTrait(Base):
    """A trait specific to a Subrace."""

    __tablename__ = "catalog_subrace_traits"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    subrace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_subraces.id", ondelete="CASCADE"),
        nullable=False,
    )
    trait_name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    mechanical_effect: Mapped[str | None] = mapped_column(String(500), nullable=True)

    subrace: Mapped[Subrace] = relationship("Subrace", back_populates="traits")


class RaceAbilityBonus(Base):
    """Ability score bonus granted by a Race or Subrace."""

    __tablename__ = "catalog_race_ability_bonuses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    race_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_races.id", ondelete="CASCADE"),
        nullable=True,
    )
    subrace_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_subraces.id", ondelete="CASCADE"),
        nullable=True,
    )
    ability: Mapped[str] = mapped_column(String(3), nullable=False)
    bonus: Mapped[int] = mapped_column(Integer, nullable=False)

    race: Mapped[Race | None] = relationship(
        "Race",
        primaryjoin="RaceAbilityBonus.race_id == Race.id",
        back_populates="ability_bonuses",
    )
    subrace: Mapped[Subrace | None] = relationship(
        "Subrace",
        primaryjoin="RaceAbilityBonus.subrace_id == Subrace.id",
        back_populates="ability_bonuses",
    )


class ClassDefinition(Base):
    """A character class definition from the SRD or a campaign homebrew."""

    __tablename__ = "catalog_class_definitions"
    __table_args__ = (
        CheckConstraint(
            _CUSTOM_CAMPAIGN_SCOPE_SQL,
            name="ck_catalog_class_definitions_custom_campaign_scope",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    hit_die: Mapped[int] = mapped_column(Integer, nullable=False)
    primary_ability: Mapped[str] = mapped_column(String(100), nullable=False)
    saving_throw_proficiencies: Mapped[str] = mapped_column(String(100), nullable=False)
    is_custom: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # FK to users.id / campaigns.id — enforced at DB level in migration.
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    campaign_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    level_features: Mapped[list[ClassLevelFeature]] = relationship(
        "ClassLevelFeature",
        back_populates="class_definition",
        cascade="all, delete-orphan",
    )
    subclasses: Mapped[list[SubclassDefinition]] = relationship(
        "SubclassDefinition",
        back_populates="class_definition",
        cascade="all, delete-orphan",
    )


class ClassLevelFeature(Base):
    """A feature granted to a class at a specific level."""

    __tablename__ = "catalog_class_level_features"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    class_definition_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_class_definitions.id", ondelete="CASCADE"),
        nullable=False,
    )
    level: Mapped[int] = mapped_column(Integer, nullable=False)
    feature_name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    mechanical_effect: Mapped[str | None] = mapped_column(String(500), nullable=True)

    class_definition: Mapped[ClassDefinition] = relationship(
        "ClassDefinition", back_populates="level_features"
    )


class SubclassDefinition(Base):
    """A subclass (archetype) for a ClassDefinition."""

    __tablename__ = "catalog_subclass_definitions"
    __table_args__ = (
        CheckConstraint(
            _CUSTOM_CAMPAIGN_SCOPE_SQL,
            name="ck_catalog_subclass_definitions_custom_campaign_scope",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    class_definition_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_class_definitions.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    is_custom: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # FK to users.id / campaigns.id — enforced at DB level in migration.
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    campaign_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    class_definition: Mapped[ClassDefinition] = relationship(
        "ClassDefinition", back_populates="subclasses"
    )


class Spell(Base):
    """A spell from the SRD."""

    __tablename__ = "catalog_spells"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    level: Mapped[int] = mapped_column(Integer, nullable=False)
    school: Mapped[str] = mapped_column(String(50), nullable=False)
    casting_time: Mapped[str] = mapped_column(String(100), nullable=False)
    range: Mapped[str] = mapped_column(String(100), nullable=False)
    duration: Mapped[str] = mapped_column(String(100), nullable=False)
    components: Mapped[str] = mapped_column(String(100), nullable=False)
    ritual: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    concentration: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    higher_levels: Mapped[str | None] = mapped_column(Text, nullable=True)


class Item(Base):
    """An equipment item from the SRD."""

    __tablename__ = "catalog_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    item_type: Mapped[str] = mapped_column(String(20), nullable=False)
    rarity: Mapped[str | None] = mapped_column(String(20), nullable=True)
    weight: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    cost: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    properties: Mapped[str | None] = mapped_column(String(500), nullable=True)

    weapon_detail: Mapped[WeaponDetail | None] = relationship(
        "WeaponDetail",
        back_populates="item",
        uselist=False,
        cascade="all, delete-orphan",
    )
    armor_detail: Mapped[ArmorDetail | None] = relationship(
        "ArmorDetail",
        back_populates="item",
        uselist=False,
        cascade="all, delete-orphan",
    )


class WeaponDetail(Base):
    """Combat statistics for a weapon Item."""

    __tablename__ = "catalog_weapon_details"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_items.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    damage_dice: Mapped[str] = mapped_column(String(20), nullable=False)
    damage_type: Mapped[str] = mapped_column(String(30), nullable=False)
    weapon_range: Mapped[str] = mapped_column(String(50), nullable=False)
    weapon_properties: Mapped[str | None] = mapped_column(String(500), nullable=True)

    item: Mapped[Item] = relationship("Item", back_populates="weapon_detail")


class ArmorDetail(Base):
    """Defense statistics for an armor Item."""

    __tablename__ = "catalog_armor_details"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_items.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    base_ac: Mapped[int] = mapped_column(Integer, nullable=False)
    dex_bonus_cap: Mapped[int | None] = mapped_column(Integer, nullable=True)
    stealth_disadvantage: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    strength_requirement: Mapped[int | None] = mapped_column(Integer, nullable=True)

    item: Mapped[Item] = relationship("Item", back_populates="armor_detail")


# --- Fixed vocabulary (SRD 2014 §7.4.1) ------------------------------------
#
# Small, low-cardinality reference tables with no complex relations. Each has
# a base table (`CatalogEntityMixin`: id/index/is_custom/campaign_id/
# created_by_id) and an `_i18n` sibling (`CatalogI18nMixin`: id/locale) — see
# `app.catalog.mixins` for the full convention.


class AbilityScoreDefinition(CatalogEntityMixin, Base):
    """One of the six core ability scores (str, dex, con, int, wis, cha)."""

    __tablename__ = "catalog_ability_score_definitions"


class AbilityScoreDefinitionI18n(CatalogI18nMixin, Base):
    """Translated text for an AbilityScoreDefinition."""

    __tablename__ = "catalog_ability_score_definitions_i18n"
    __table_args__ = (
        UniqueConstraint(
            "entity_id", "locale", name="uq_catalog_ability_score_definitions_i18n"
        ),
    )

    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_ability_score_definitions.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    desc: Mapped[str] = mapped_column(Text, nullable=False, default="")


class SkillDefinition(CatalogEntityMixin, Base):
    """A skill tied to a governing ability score (e.g. Stealth -> dex)."""

    __tablename__ = "catalog_skill_definitions"

    ability_score_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_ability_score_definitions.id"),
        nullable=False,
    )


class SkillDefinitionI18n(CatalogI18nMixin, Base):
    """Translated text for a SkillDefinition."""

    __tablename__ = "catalog_skill_definitions_i18n"
    __table_args__ = (
        UniqueConstraint(
            "entity_id", "locale", name="uq_catalog_skill_definitions_i18n"
        ),
    )

    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_skill_definitions.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    desc: Mapped[str] = mapped_column(Text, nullable=False, default="")


class Alignment(CatalogEntityMixin, Base):
    """A moral/ethical alignment (e.g. Lawful Good)."""

    __tablename__ = "catalog_alignments"


class AlignmentI18n(CatalogI18nMixin, Base):
    """Translated text for an Alignment."""

    __tablename__ = "catalog_alignments_i18n"
    __table_args__ = (
        UniqueConstraint("entity_id", "locale", name="uq_catalog_alignments_i18n"),
    )

    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_alignments.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    abbreviation: Mapped[str] = mapped_column(String(5), nullable=False)
    desc: Mapped[str] = mapped_column(Text, nullable=False, default="")


class Condition(CatalogEntityMixin, Base):
    """A status condition (e.g. Blinded, Poisoned)."""

    __tablename__ = "catalog_conditions"


class ConditionI18n(CatalogI18nMixin, Base):
    """Translated text for a Condition."""

    __tablename__ = "catalog_conditions_i18n"
    __table_args__ = (
        UniqueConstraint("entity_id", "locale", name="uq_catalog_conditions_i18n"),
    )

    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_conditions.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    desc: Mapped[str] = mapped_column(Text, nullable=False, default="")


class DamageType(CatalogEntityMixin, Base):
    """A damage type (e.g. Fire, Slashing)."""

    __tablename__ = "catalog_damage_types"


class DamageTypeI18n(CatalogI18nMixin, Base):
    """Translated text for a DamageType."""

    __tablename__ = "catalog_damage_types_i18n"
    __table_args__ = (
        UniqueConstraint("entity_id", "locale", name="uq_catalog_damage_types_i18n"),
    )

    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_damage_types.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    desc: Mapped[str] = mapped_column(Text, nullable=False, default="")


class MagicSchool(CatalogEntityMixin, Base):
    """A school of magic (e.g. Evocation, Necromancy)."""

    __tablename__ = "catalog_magic_schools"


class MagicSchoolI18n(CatalogI18nMixin, Base):
    """Translated text for a MagicSchool."""

    __tablename__ = "catalog_magic_schools_i18n"
    __table_args__ = (
        UniqueConstraint("entity_id", "locale", name="uq_catalog_magic_schools_i18n"),
    )

    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_magic_schools.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    desc: Mapped[str | None] = mapped_column(Text, nullable=True)


class Language(CatalogEntityMixin, Base):
    """A language spoken in the setting (e.g. Common, Elvish)."""

    __tablename__ = "catalog_languages"

    language_type: Mapped[str] = mapped_column(
        SAEnum(LanguageType, name="languagetype"),
        nullable=False,
        default=LanguageType.standard,
    )


class LanguageI18n(CatalogI18nMixin, Base):
    """Translated text for a Language."""

    __tablename__ = "catalog_languages_i18n"
    __table_args__ = (
        UniqueConstraint("entity_id", "locale", name="uq_catalog_languages_i18n"),
    )

    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_languages.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    desc: Mapped[str] = mapped_column(Text, nullable=False, default="")
    script: Mapped[str | None] = mapped_column(String(100), nullable=True)
    typical_speakers: Mapped[str | None] = mapped_column(String(200), nullable=True)


class WeaponProperty(CatalogEntityMixin, Base):
    """A weapon property (e.g. Finesse, Heavy, Two-Handed)."""

    __tablename__ = "catalog_weapon_properties"


class WeaponPropertyI18n(CatalogI18nMixin, Base):
    """Translated text for a WeaponProperty."""

    __tablename__ = "catalog_weapon_properties_i18n"
    __table_args__ = (
        UniqueConstraint(
            "entity_id", "locale", name="uq_catalog_weapon_properties_i18n"
        ),
    )

    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_weapon_properties.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    desc: Mapped[str] = mapped_column(Text, nullable=False, default="")


# --- Proficiencies (SRD 2014 §7.4.3) ----------------------------------------
#
# A Proficiency has three nullable, mutually-exclusive reference FKs instead
# of a generic polymorphic reference — which one is populated depends on
# `proficiency_type` (see `app.catalog.domain.validate_proficiency_reference_scope`).


class Proficiency(CatalogEntityMixin, Base):
    """A proficiency (skill, saving throw, weapon, armor, tool, or other)."""

    __tablename__ = "catalog_proficiencies"
    _extra_table_args: ClassVar[tuple[CheckConstraint, ...]] = (
        CheckConstraint(
            "(proficiency_type = 'skill' AND skill_id IS NOT NULL "
            "  AND ability_score_id IS NULL AND equipment_category_id IS NULL)"
            " OR (proficiency_type = 'saving_throw' AND ability_score_id IS NOT NULL "
            "  AND skill_id IS NULL AND equipment_category_id IS NULL)"
            " OR (proficiency_type IN ('weapon', 'armor', 'tool') "
            "  AND equipment_category_id IS NOT NULL "
            "  AND skill_id IS NULL AND ability_score_id IS NULL)"
            " OR (proficiency_type = 'other' AND skill_id IS NULL "
            "  AND ability_score_id IS NULL AND equipment_category_id IS NULL)",
            name="ck_catalog_proficiencies_reference_scope",
        ),
    )

    proficiency_type: Mapped[str] = mapped_column(
        SAEnum(ProficiencyType, name="proficiencytype"), nullable=False
    )
    skill_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("catalog_skill_definitions.id"), nullable=True
    )
    ability_score_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_ability_score_definitions.id"),
        nullable=True,
    )
    # FK to catalog_equipment_categories.id once the Equipamento story lands —
    # plain UUID for now, mirroring how campaign_id predates the Campaigns
    # domain (see `CatalogEntityMixin`).
    equipment_category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )


class ProficiencyI18n(CatalogI18nMixin, Base):
    """Translated text for a Proficiency."""

    __tablename__ = "catalog_proficiencies_i18n"
    __table_args__ = (
        UniqueConstraint("entity_id", "locale", name="uq_catalog_proficiencies_i18n"),
    )

    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_proficiencies.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)


class ProficiencyClass(Base):
    """Junction: a ClassDefinition grants a Proficiency by default."""

    __tablename__ = "catalog_proficiency_classes"
    __table_args__ = (
        UniqueConstraint(
            "proficiency_id",
            "class_definition_id",
            name="uq_catalog_proficiency_classes",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    proficiency_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_proficiencies.id", ondelete="CASCADE"),
        nullable=False,
    )
    class_definition_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_class_definitions.id", ondelete="CASCADE"),
        nullable=False,
    )


class ProficiencyRace(Base):
    """Junction: a Race grants a Proficiency by default."""

    __tablename__ = "catalog_proficiency_races"
    __table_args__ = (
        UniqueConstraint(
            "proficiency_id", "race_id", name="uq_catalog_proficiency_races"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    proficiency_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_proficiencies.id", ondelete="CASCADE"),
        nullable=False,
    )
    race_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_races.id", ondelete="CASCADE"),
        nullable=False,
    )
