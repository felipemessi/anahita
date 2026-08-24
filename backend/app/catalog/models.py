"""SQLAlchemy models for the catalog domain (D&D 5e SRD reference data)."""

import uuid
from typing import ClassVar

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Float,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.catalog.domain import (
    CreatureSize,
    DamageModifierType,
    FeaturePrerequisiteType,
    ItemType,
    LanguageType,
    ProficiencyType,
)
from app.catalog.mixins import CatalogEntityMixin, CatalogI18nMixin
from app.database import Base

#: Reused by every catalog table that carries `is_custom`/`campaign_id` but
#: predates `CatalogEntityMixin` (Race, ClassDefinition, SubclassDefinition) —
#: see `app.catalog.mixins.CatalogEntityMixin` for the canonical version.
_CUSTOM_CAMPAIGN_SCOPE_SQL = (
    "(NOT is_custom AND campaign_id IS NULL) OR (is_custom AND campaign_id IS NOT NULL)"
)


class Race(Base):
    """A playable race from the SRD or a campaign homebrew.

    Translatable text (`name`, `description`, `age`, `alignment_desc`,
    `size_description`, `language_desc`) lives in `RaceI18n` — see
    `app.catalog.mixins` for the `_i18n` convention.
    """

    __tablename__ = "catalog_races"
    __table_args__ = (
        CheckConstraint(
            _CUSTOM_CAMPAIGN_SCOPE_SQL, name="ck_catalog_races_custom_campaign_scope"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    index: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    speed: Mapped[int] = mapped_column(Integer, nullable=False)
    size: Mapped[str] = mapped_column(
        String(20), nullable=False, default=CreatureSize.medium.value
    )
    darkvision_range: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
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


class RaceI18n(CatalogI18nMixin, Base):
    """Translated text for a Race."""

    __tablename__ = "catalog_races_i18n"
    __table_args__ = (
        UniqueConstraint("entity_id", "locale", name="uq_catalog_races_i18n"),
    )

    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_races.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    age: Mapped[str] = mapped_column(Text, nullable=False, default="")
    alignment_desc: Mapped[str] = mapped_column(Text, nullable=False, default="")
    size_description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    language_desc: Mapped[str] = mapped_column(Text, nullable=False, default="")


class RaceTrait(Base):
    """A racial trait associated with a Race.

    Translatable text (`trait_name`, `description`) lives in `RaceTraitI18n`.
    """

    __tablename__ = "catalog_race_traits"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    race_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_races.id", ondelete="CASCADE"),
        nullable=False,
    )
    mechanical_effect: Mapped[str | None] = mapped_column(String(500), nullable=True)

    race: Mapped[Race] = relationship("Race", back_populates="traits")


class RaceTraitI18n(CatalogI18nMixin, Base):
    """Translated text for a RaceTrait."""

    __tablename__ = "catalog_race_traits_i18n"
    __table_args__ = (
        UniqueConstraint("entity_id", "locale", name="uq_catalog_race_traits_i18n"),
    )

    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_race_traits.id", ondelete="CASCADE"),
        nullable=False,
    )
    trait_name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")


class Subrace(Base):
    """A subrace variant of a Race.

    Translatable text (`name`, `description`) lives in `SubraceI18n`.
    """

    __tablename__ = "catalog_subraces"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    race_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_races.id", ondelete="CASCADE"),
        nullable=False,
    )
    index: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)

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


class SubraceI18n(CatalogI18nMixin, Base):
    """Translated text for a Subrace."""

    __tablename__ = "catalog_subraces_i18n"
    __table_args__ = (
        UniqueConstraint("entity_id", "locale", name="uq_catalog_subraces_i18n"),
    )

    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_subraces.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")


class SubraceTrait(Base):
    """A trait specific to a Subrace.

    Translatable text (`trait_name`, `description`) lives in `SubraceTraitI18n`.
    """

    __tablename__ = "catalog_subrace_traits"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    subrace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_subraces.id", ondelete="CASCADE"),
        nullable=False,
    )
    mechanical_effect: Mapped[str | None] = mapped_column(String(500), nullable=True)

    subrace: Mapped[Subrace] = relationship("Subrace", back_populates="traits")


class SubraceTraitI18n(CatalogI18nMixin, Base):
    """Translated text for a SubraceTrait."""

    __tablename__ = "catalog_subrace_traits_i18n"
    __table_args__ = (
        UniqueConstraint("entity_id", "locale", name="uq_catalog_subrace_traits_i18n"),
    )

    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_subrace_traits.id", ondelete="CASCADE"),
        nullable=False,
    )
    trait_name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")


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
    """A character class definition from the SRD or a campaign homebrew.

    Translatable text (`name`) lives in `ClassDefinitionI18n` — see
    `app.catalog.mixins` for the `_i18n` convention.
    """

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
    index: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    hit_die: Mapped[int] = mapped_column(Integer, nullable=False)
    primary_ability: Mapped[str] = mapped_column(String(100), nullable=False)
    saving_throw_proficiencies: Mapped[str] = mapped_column(String(100), nullable=False)
    # Short ability code (`str`/`dex`/`con`/`int`/`wis`/`cha`) governing this
    # class's spells, or NULL for non-caster classes (PRD §7.4.4 progression;
    # consumed by `engine/spellcasting.py`).
    spellcasting_ability: Mapped[str | None] = mapped_column(
        String(3), nullable=True
    )
    is_custom: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # FK to users.id / campaigns.id — enforced at DB level in migration.
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    campaign_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    features: Mapped[list[Feature]] = relationship(
        "Feature",
        primaryjoin="Feature.class_definition_id == ClassDefinition.id",
        back_populates="class_definition",
        cascade="all, delete-orphan",
    )
    class_levels: Mapped[list[ClassLevel]] = relationship(
        "ClassLevel",
        back_populates="class_definition",
        cascade="all, delete-orphan",
    )
    subclasses: Mapped[list[SubclassDefinition]] = relationship(
        "SubclassDefinition",
        back_populates="class_definition",
        cascade="all, delete-orphan",
    )


class ClassDefinitionI18n(CatalogI18nMixin, Base):
    """Translated text for a ClassDefinition."""

    __tablename__ = "catalog_class_definitions_i18n"
    __table_args__ = (
        UniqueConstraint(
            "entity_id", "locale", name="uq_catalog_class_definitions_i18n"
        ),
    )

    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_class_definitions.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)


class SubclassDefinition(Base):
    """A subclass (archetype) for a ClassDefinition.

    Translatable text (`name`, `description`, `flavor`) lives in
    `SubclassDefinitionI18n`.
    """

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
    index: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
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
    features: Mapped[list[Feature]] = relationship(
        "Feature",
        primaryjoin="Feature.subclass_definition_id == SubclassDefinition.id",
        back_populates="subclass_definition",
        cascade="all, delete-orphan",
    )


class SubclassDefinitionI18n(CatalogI18nMixin, Base):
    """Translated text for a SubclassDefinition."""

    __tablename__ = "catalog_subclass_definitions_i18n"
    __table_args__ = (
        UniqueConstraint(
            "entity_id", "locale", name="uq_catalog_subclass_definitions_i18n"
        ),
    )

    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_subclass_definitions.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    flavor: Mapped[str] = mapped_column(Text, nullable=False, default="")


class Feature(Base):
    """A feature granted by a class or subclass at a given level.

    Generalizes the old `ClassLevelFeature` model: covers class *and*
    subclass features, including sub-features (e.g. a Fighting Style choice
    nested under a broader feature) via `parent_feature_id`. Exactly one of
    `class_definition_id`/`subclass_definition_id` is set. Translatable text
    (`feature_name`, `description`) lives in `FeatureI18n`.
    """

    __tablename__ = "catalog_features"
    __table_args__ = (
        CheckConstraint(
            _CUSTOM_CAMPAIGN_SCOPE_SQL,
            name="ck_catalog_features_custom_campaign_scope",
        ),
        CheckConstraint(
            "(class_definition_id IS NOT NULL AND subclass_definition_id IS NULL)"
            " OR (class_definition_id IS NULL AND subclass_definition_id IS NOT NULL)",
            name="ck_catalog_features_owner_scope",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    index: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    class_definition_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_class_definitions.id", ondelete="CASCADE"),
        nullable=True,
    )
    subclass_definition_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_subclass_definitions.id", ondelete="CASCADE"),
        nullable=True,
    )
    level: Mapped[int] = mapped_column(Integer, nullable=False)
    parent_feature_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_features.id", ondelete="CASCADE"),
        nullable=True,
    )
    mechanical_effect: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_custom: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # FK to users.id / campaigns.id — enforced at DB level in migration.
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    campaign_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    class_definition: Mapped[ClassDefinition | None] = relationship(
        "ClassDefinition",
        primaryjoin="Feature.class_definition_id == ClassDefinition.id",
        back_populates="features",
    )
    subclass_definition: Mapped[SubclassDefinition | None] = relationship(
        "SubclassDefinition",
        primaryjoin="Feature.subclass_definition_id == SubclassDefinition.id",
        back_populates="features",
    )
    prerequisites: Mapped[list[FeaturePrerequisite]] = relationship(
        "FeaturePrerequisite",
        primaryjoin="FeaturePrerequisite.feature_id == Feature.id",
        back_populates="feature",
        cascade="all, delete-orphan",
    )


class FeatureI18n(CatalogI18nMixin, Base):
    """Translated text for a Feature."""

    __tablename__ = "catalog_features_i18n"
    __table_args__ = (
        UniqueConstraint("entity_id", "locale", name="uq_catalog_features_i18n"),
    )

    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_features.id", ondelete="CASCADE"),
        nullable=False,
    )
    feature_name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")


class FeaturePrerequisite(Base):
    """A prerequisite (level, another feature, or a spell) gating a Feature."""

    __tablename__ = "catalog_feature_prerequisites"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    feature_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_features.id", ondelete="CASCADE"),
        nullable=False,
    )
    prerequisite_type: Mapped[str] = mapped_column(
        SAEnum(FeaturePrerequisiteType, name="featureprerequisitetype"),
        nullable=False,
    )
    level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    required_feature_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_features.id", ondelete="CASCADE"),
        nullable=True,
    )
    spell_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_spells.id", ondelete="CASCADE"),
        nullable=True,
    )

    feature: Mapped[Feature] = relationship(
        "Feature",
        primaryjoin="FeaturePrerequisite.feature_id == Feature.id",
        back_populates="prerequisites",
    )


class ClassLevel(Base):
    """One row of a class's (or subclass's) level-by-level progression table.

    `subclass_definition_id` is nullable: `NULL` rows are the base class
    progression (proficiency bonus, ability score improvements); rows with it
    set track a subclass's own per-level grants. Unique on
    `(class_definition_id, subclass_definition_id, level)`.
    """

    __tablename__ = "catalog_class_levels"
    __table_args__ = (
        UniqueConstraint(
            "class_definition_id",
            "subclass_definition_id",
            "level",
            name="uq_catalog_class_levels",
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
    subclass_definition_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_subclass_definitions.id", ondelete="CASCADE"),
        nullable=True,
    )
    level: Mapped[int] = mapped_column(Integer, nullable=False)
    proficiency_bonus: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ability_score_bonuses: Mapped[int | None] = mapped_column(Integer, nullable=True)

    class_definition: Mapped[ClassDefinition] = relationship(
        "ClassDefinition", back_populates="class_levels"
    )
    level_features: Mapped[list[ClassLevelFeature]] = relationship(
        "ClassLevelFeature", back_populates="class_level", cascade="all, delete-orphan"
    )
    spell_slots: Mapped[list[ClassLevelSpellSlot]] = relationship(
        "ClassLevelSpellSlot",
        back_populates="class_level",
        cascade="all, delete-orphan",
    )
    resources: Mapped[list[ClassLevelResource]] = relationship(
        "ClassLevelResource", back_populates="class_level", cascade="all, delete-orphan"
    )


class ClassLevelFeature(Base):
    """Junction: a Feature is granted at a specific ClassLevel row."""

    __tablename__ = "catalog_class_level_features"
    __table_args__ = (
        UniqueConstraint(
            "class_level_id", "feature_id", name="uq_catalog_class_level_features"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    class_level_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_class_levels.id", ondelete="CASCADE"),
        nullable=False,
    )
    feature_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_features.id", ondelete="CASCADE"),
        nullable=False,
    )

    class_level: Mapped[ClassLevel] = relationship(
        "ClassLevel", back_populates="level_features"
    )
    feature: Mapped[Feature] = relationship("Feature")


class ClassLevelSpellSlot(Base):
    """Number of spell slots (or cantrips known, `spell_level=0`) at a ClassLevel."""

    __tablename__ = "catalog_class_level_spell_slots"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    class_level_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_class_levels.id", ondelete="CASCADE"),
        nullable=False,
    )
    spell_level: Mapped[int] = mapped_column(Integer, nullable=False)
    slot_count: Mapped[int] = mapped_column(Integer, nullable=False)

    class_level: Mapped[ClassLevel] = relationship(
        "ClassLevel", back_populates="spell_slots"
    )


class ClassLevelResource(Base):
    """A class-specific mechanical resource at a ClassLevel (e.g. rage_count).

    Reuses the structured-vocabulary pattern already used for
    `mechanical_effect` elsewhere in the catalog (PRD §8.3): `resource_key`
    identifies the mechanic (`rage_count`, `ki_points`, `sneak_attack_dice`,
    ...) and `value` carries its value as a string (`"3"`, `"2d6"`).
    """

    __tablename__ = "catalog_class_level_resources"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    class_level_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_class_levels.id", ondelete="CASCADE"),
        nullable=False,
    )
    resource_key: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[str] = mapped_column(String(100), nullable=False)

    class_level: Mapped[ClassLevel] = relationship(
        "ClassLevel", back_populates="resources"
    )


class Spell(Base):
    """A spell from the SRD or a campaign homebrew.

    Translatable text (`name`, `description`, `higher_levels`) lives in
    `SpellI18n` — see `app.catalog.mixins` for the `_i18n` convention.
    """

    __tablename__ = "catalog_spells"
    __table_args__ = (
        CheckConstraint(
            _CUSTOM_CAMPAIGN_SCOPE_SQL, name="ck_catalog_spells_custom_campaign_scope"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    index: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    level: Mapped[int] = mapped_column(Integer, nullable=False)
    magic_school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_magic_schools.id"),
        nullable=False,
    )
    casting_time: Mapped[str] = mapped_column(String(100), nullable=False)
    range: Mapped[str] = mapped_column(String(100), nullable=False)
    duration: Mapped[str] = mapped_column(String(100), nullable=False)
    components: Mapped[str] = mapped_column(String(100), nullable=False)
    ritual: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    concentration: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_custom: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # FK to users.id / campaigns.id — enforced at DB level in migration.
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    campaign_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    magic_school: Mapped[MagicSchool] = relationship("MagicSchool")
    classes: Mapped[list[SpellClass]] = relationship(
        "SpellClass", back_populates="spell", cascade="all, delete-orphan"
    )


class SpellI18n(CatalogI18nMixin, Base):
    """Translated text for a Spell."""

    __tablename__ = "catalog_spells_i18n"
    __table_args__ = (
        UniqueConstraint("entity_id", "locale", name="uq_catalog_spells_i18n"),
    )

    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_spells.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    higher_levels: Mapped[str | None] = mapped_column(Text, nullable=True)


class SpellClass(Base):
    """Junction: a ClassDefinition can cast a Spell."""

    __tablename__ = "catalog_spell_classes"
    __table_args__ = (
        UniqueConstraint(
            "spell_id", "class_definition_id", name="uq_catalog_spell_classes"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    spell_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_spells.id", ondelete="CASCADE"),
        nullable=False,
    )
    class_definition_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_class_definitions.id", ondelete="CASCADE"),
        nullable=False,
    )

    spell: Mapped[Spell] = relationship("Spell", back_populates="classes")
    class_definition: Mapped[ClassDefinition] = relationship("ClassDefinition")


class EquipmentCategory(CatalogEntityMixin, Base):
    """A category of equipment (e.g. Simple Weapons, Heavy Armor)."""

    __tablename__ = "catalog_equipment_categories"


class EquipmentCategoryI18n(CatalogI18nMixin, Base):
    """Translated text for an EquipmentCategory."""

    __tablename__ = "catalog_equipment_categories_i18n"
    __table_args__ = (
        UniqueConstraint(
            "entity_id", "locale", name="uq_catalog_equipment_categories_i18n"
        ),
    )

    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_equipment_categories.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)


class Item(Base):
    """An equipment item from the SRD or a campaign homebrew.

    Translatable text (`name`, `description`) lives in `ItemI18n` — see
    `app.catalog.mixins` for the `_i18n` convention.
    """

    __tablename__ = "catalog_items"
    __table_args__ = (
        CheckConstraint(
            _CUSTOM_CAMPAIGN_SCOPE_SQL, name="ck_catalog_items_custom_campaign_scope"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    index: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    item_type: Mapped[str] = mapped_column(
        SAEnum(ItemType, name="itemtype"), nullable=False
    )
    equipment_category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_equipment_categories.id"),
        nullable=False,
    )
    rarity: Mapped[str | None] = mapped_column(String(20), nullable=True)
    weight: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    cost: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_custom: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # FK to users.id / campaigns.id — enforced at DB level in migration.
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    campaign_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    equipment_category: Mapped[EquipmentCategory] = relationship("EquipmentCategory")
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
    properties: Mapped[list[ItemProperty]] = relationship(
        "ItemProperty", back_populates="item", cascade="all, delete-orphan"
    )


class ItemI18n(CatalogI18nMixin, Base):
    """Translated text for an Item."""

    __tablename__ = "catalog_items_i18n"
    __table_args__ = (
        UniqueConstraint("entity_id", "locale", name="uq_catalog_items_i18n"),
    )

    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_items.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")


class ItemProperty(Base):
    """Junction: an Item (typically a weapon) carries a WeaponProperty."""

    __tablename__ = "catalog_item_properties"
    __table_args__ = (
        UniqueConstraint(
            "item_id", "weapon_property_id", name="uq_catalog_item_properties"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_items.id", ondelete="CASCADE"),
        nullable=False,
    )
    weapon_property_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_weapon_properties.id", ondelete="CASCADE"),
        nullable=False,
    )

    item: Mapped[Item] = relationship("Item", back_populates="properties")
    weapon_property: Mapped[WeaponProperty] = relationship("WeaponProperty")


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
    damage_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_damage_types.id"),
        nullable=False,
    )
    weapon_range: Mapped[str] = mapped_column(String(50), nullable=False)

    item: Mapped[Item] = relationship("Item", back_populates="weapon_detail")
    damage_type: Mapped[DamageType] = relationship("DamageType")


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


class MagicItem(CatalogEntityMixin, Base):
    """A magic item from the SRD or a campaign homebrew.

    `variant_of_id` links a numbered variant (e.g. a +2 version) back to its
    base magic item (e.g. +1); `is_variant` marks which of the two a row is.
    Translatable text (`name`, `description`) lives in `MagicItemI18n`.
    """

    __tablename__ = "catalog_magic_items"
    _extra_table_args: ClassVar[tuple[ForeignKeyConstraint, ...]] = (
        ForeignKeyConstraint(
            ["variant_of_id"], ["catalog_magic_items.id"], ondelete="CASCADE"
        ),
    )

    equipment_category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_equipment_categories.id"),
        nullable=False,
    )
    rarity: Mapped[str] = mapped_column(String(20), nullable=False)
    is_variant: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    variant_of_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    equipment_category: Mapped[EquipmentCategory] = relationship("EquipmentCategory")
    variant_of: Mapped[MagicItem | None] = relationship(
        "MagicItem", remote_side="MagicItem.id", back_populates="variants"
    )
    variants: Mapped[list[MagicItem]] = relationship(
        "MagicItem", back_populates="variant_of"
    )


class MagicItemI18n(CatalogI18nMixin, Base):
    """Translated text for a MagicItem."""

    __tablename__ = "catalog_magic_items_i18n"
    __table_args__ = (
        UniqueConstraint("entity_id", "locale", name="uq_catalog_magic_items_i18n"),
    )

    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_magic_items.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")


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
    equipment_category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_equipment_categories.id"),
        nullable=True,
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


# --- Backgrounds and Feats (SRD 2014 §7.4.7) --------------------------------


class Background(CatalogEntityMixin, Base):
    """A character background from the SRD or a campaign homebrew.

    Translatable text (`name`, `personality_traits`, `ideals`, `bonds`,
    `flaws`) lives in `BackgroundI18n`.
    """

    __tablename__ = "catalog_backgrounds"

    proficiencies: Mapped[list[BackgroundProficiency]] = relationship(
        "BackgroundProficiency",
        back_populates="background",
        cascade="all, delete-orphan",
    )
    equipment: Mapped[list[BackgroundEquipment]] = relationship(
        "BackgroundEquipment",
        back_populates="background",
        cascade="all, delete-orphan",
    )
    feature: Mapped[BackgroundFeature | None] = relationship(
        "BackgroundFeature",
        back_populates="background",
        uselist=False,
        cascade="all, delete-orphan",
    )


class BackgroundI18n(CatalogI18nMixin, Base):
    """Translated text for a Background.

    The SRD presents `personality_traits`/`ideals`/`bonds`/`flaws` as
    roll-tables; here they're descriptive free text (a future phase could
    normalize them into a rollable-options table if the UI needs to roll or
    pick from them directly).
    """

    __tablename__ = "catalog_backgrounds_i18n"
    __table_args__ = (
        UniqueConstraint("entity_id", "locale", name="uq_catalog_backgrounds_i18n"),
    )

    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_backgrounds.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    personality_traits: Mapped[str] = mapped_column(Text, nullable=False, default="")
    ideals: Mapped[str] = mapped_column(Text, nullable=False, default="")
    bonds: Mapped[str] = mapped_column(Text, nullable=False, default="")
    flaws: Mapped[str] = mapped_column(Text, nullable=False, default="")


class BackgroundProficiency(Base):
    """Junction: a Background grants a Proficiency by default."""

    __tablename__ = "catalog_background_proficiencies"
    __table_args__ = (
        UniqueConstraint(
            "background_id",
            "proficiency_id",
            name="uq_catalog_background_proficiencies",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    background_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_backgrounds.id", ondelete="CASCADE"),
        nullable=False,
    )
    proficiency_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_proficiencies.id", ondelete="CASCADE"),
        nullable=False,
    )

    background: Mapped[Background] = relationship(
        "Background", back_populates="proficiencies"
    )
    proficiency: Mapped[Proficiency] = relationship("Proficiency")


class BackgroundEquipment(Base):
    """Junction: a Background grants a starting Item, in a given quantity."""

    __tablename__ = "catalog_background_equipment"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    background_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_backgrounds.id", ondelete="CASCADE"),
        nullable=False,
    )
    item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_items.id", ondelete="CASCADE"),
        nullable=False,
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    background: Mapped[Background] = relationship(
        "Background", back_populates="equipment"
    )
    item: Mapped[Item] = relationship("Item")


class BackgroundFeature(Base):
    """The single signature feature granted by a Background (1:1).

    Translatable text (`feature_name`, `description`) lives in
    `BackgroundFeatureI18n`.
    """

    __tablename__ = "catalog_background_features"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    background_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_backgrounds.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    background: Mapped[Background] = relationship(
        "Background", back_populates="feature"
    )


class BackgroundFeatureI18n(CatalogI18nMixin, Base):
    """Translated text for a BackgroundFeature."""

    __tablename__ = "catalog_background_features_i18n"
    __table_args__ = (
        UniqueConstraint(
            "entity_id", "locale", name="uq_catalog_background_features_i18n"
        ),
    )

    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_background_features.id", ondelete="CASCADE"),
        nullable=False,
    )
    feature_name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")


class Feat(CatalogEntityMixin, Base):
    """A feat from the SRD or a campaign homebrew.

    Translatable text (`name`, `description`) lives in `FeatI18n`.
    """

    __tablename__ = "catalog_feats"

    prerequisites: Mapped[list[FeatPrerequisite]] = relationship(
        "FeatPrerequisite", back_populates="feat", cascade="all, delete-orphan"
    )


class FeatI18n(CatalogI18nMixin, Base):
    """Translated text for a Feat."""

    __tablename__ = "catalog_feats_i18n"
    __table_args__ = (
        UniqueConstraint("entity_id", "locale", name="uq_catalog_feats_i18n"),
    )

    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_feats.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")


class FeatPrerequisite(Base):
    """An ability score minimum gating a Feat (e.g. Strength 13 for Grappler)."""

    __tablename__ = "catalog_feat_prerequisites"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    feat_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_feats.id", ondelete="CASCADE"),
        nullable=False,
    )
    ability_score_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_ability_score_definitions.id"),
        nullable=True,
    )
    minimum_score: Mapped[int] = mapped_column(Integer, nullable=False)

    feat: Mapped[Feat] = relationship("Feat", back_populates="prerequisites")


# --- Monsters / stat blocks (SRD 2014 §7.4.8) -------------------------------
#
# Replaces the loose `stat_block_id` on `NPC` (PRD §7.7, not yet modeled):
# once world-building lands, `NPC.stat_block_id` will point here. Same
# is_custom/campaign_id pattern as the rest of the catalog — a DM can create
# a homebrew monster, scoped to their campaign.


class Monster(CatalogEntityMixin, Base):
    """A monster stat block from the SRD or a campaign homebrew.

    Translatable text (`name`, `description`) lives in `MonsterI18n`.
    """

    __tablename__ = "catalog_monsters"

    size: Mapped[str] = mapped_column(
        SAEnum(CreatureSize, name="creaturesize"), nullable=False
    )
    creature_type: Mapped[str] = mapped_column(String(100), nullable=False)
    creature_subtype: Mapped[str | None] = mapped_column(String(100), nullable=True)
    alignment: Mapped[str] = mapped_column(String(100), nullable=False)
    hit_points: Mapped[int] = mapped_column(Integer, nullable=False)
    hit_dice: Mapped[str] = mapped_column(String(50), nullable=False)
    challenge_rating: Mapped[float] = mapped_column(Float, nullable=False)
    xp: Mapped[int] = mapped_column(Integer, nullable=False)
    proficiency_bonus: Mapped[int | None] = mapped_column(Integer, nullable=True)
    languages: Mapped[str] = mapped_column(String(300), nullable=False, default="")
    strength: Mapped[int] = mapped_column(Integer, nullable=False)
    dexterity: Mapped[int] = mapped_column(Integer, nullable=False)
    constitution: Mapped[int] = mapped_column(Integer, nullable=False)
    intelligence: Mapped[int] = mapped_column(Integer, nullable=False)
    wisdom: Mapped[int] = mapped_column(Integer, nullable=False)
    charisma: Mapped[int] = mapped_column(Integer, nullable=False)

    speed: Mapped[MonsterSpeed | None] = relationship(
        "MonsterSpeed",
        back_populates="monster",
        uselist=False,
        cascade="all, delete-orphan",
    )
    senses: Mapped[MonsterSense | None] = relationship(
        "MonsterSense",
        back_populates="monster",
        uselist=False,
        cascade="all, delete-orphan",
    )
    armor_classes: Mapped[list[MonsterArmorClass]] = relationship(
        "MonsterArmorClass", back_populates="monster", cascade="all, delete-orphan"
    )
    proficiencies: Mapped[list[MonsterProficiency]] = relationship(
        "MonsterProficiency", back_populates="monster", cascade="all, delete-orphan"
    )
    damage_modifiers: Mapped[list[MonsterDamageModifier]] = relationship(
        "MonsterDamageModifier", back_populates="monster", cascade="all, delete-orphan"
    )
    condition_immunities: Mapped[list[MonsterConditionImmunity]] = relationship(
        "MonsterConditionImmunity",
        back_populates="monster",
        cascade="all, delete-orphan",
    )
    actions: Mapped[list[MonsterAction]] = relationship(
        "MonsterAction", back_populates="monster", cascade="all, delete-orphan"
    )
    legendary_actions: Mapped[list[MonsterLegendaryAction]] = relationship(
        "MonsterLegendaryAction", back_populates="monster", cascade="all, delete-orphan"
    )
    reactions: Mapped[list[MonsterReaction]] = relationship(
        "MonsterReaction", back_populates="monster", cascade="all, delete-orphan"
    )
    special_abilities: Mapped[list[MonsterSpecialAbility]] = relationship(
        "MonsterSpecialAbility", back_populates="monster", cascade="all, delete-orphan"
    )


class MonsterI18n(CatalogI18nMixin, Base):
    """Translated text for a Monster."""

    __tablename__ = "catalog_monsters_i18n"
    __table_args__ = (
        UniqueConstraint("entity_id", "locale", name="uq_catalog_monsters_i18n"),
    )

    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_monsters.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")


class MonsterSpeed(Base):
    """A Monster's movement speeds (1:1)."""

    __tablename__ = "catalog_monster_speeds"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    monster_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_monsters.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    walk: Mapped[str | None] = mapped_column(String(50), nullable=True)
    burrow: Mapped[str | None] = mapped_column(String(50), nullable=True)
    climb: Mapped[str | None] = mapped_column(String(50), nullable=True)
    fly: Mapped[str | None] = mapped_column(String(50), nullable=True)
    swim: Mapped[str | None] = mapped_column(String(50), nullable=True)
    hover: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    monster: Mapped[Monster] = relationship("Monster", back_populates="speed")


class MonsterSense(Base):
    """A Monster's senses (1:1)."""

    __tablename__ = "catalog_monster_senses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    monster_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_monsters.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    passive_perception: Mapped[int] = mapped_column(Integer, nullable=False)
    blindsight: Mapped[str | None] = mapped_column(String(50), nullable=True)
    darkvision: Mapped[str | None] = mapped_column(String(50), nullable=True)
    tremorsense: Mapped[str | None] = mapped_column(String(50), nullable=True)
    truesight: Mapped[str | None] = mapped_column(String(50), nullable=True)

    monster: Mapped[Monster] = relationship("Monster", back_populates="senses")


class MonsterArmorClass(Base):
    """One AC entry for a Monster (it can have several, e.g. natural + shield)."""

    __tablename__ = "catalog_monster_armor_classes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    monster_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_monsters.id", ondelete="CASCADE"),
        nullable=False,
    )
    ac_type: Mapped[str] = mapped_column(String(50), nullable=False)
    value: Mapped[int] = mapped_column(Integer, nullable=False)
    condition_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("catalog_conditions.id"), nullable=True
    )
    description: Mapped[str | None] = mapped_column(String(200), nullable=True)

    monster: Mapped[Monster] = relationship("Monster", back_populates="armor_classes")


class MonsterProficiency(Base):
    """A Monster's proficiency bonus applied to a specific Proficiency (skill/save)."""

    __tablename__ = "catalog_monster_proficiencies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    monster_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_monsters.id", ondelete="CASCADE"),
        nullable=False,
    )
    proficiency_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_proficiencies.id", ondelete="CASCADE"),
        nullable=False,
    )
    value: Mapped[int] = mapped_column(Integer, nullable=False)

    monster: Mapped[Monster] = relationship("Monster", back_populates="proficiencies")
    proficiency: Mapped[Proficiency] = relationship("Proficiency")


class MonsterDamageModifier(Base):
    """A Monster's vulnerability, resistance, or immunity to a DamageType."""

    __tablename__ = "catalog_monster_damage_modifiers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    monster_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_monsters.id", ondelete="CASCADE"),
        nullable=False,
    )
    damage_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_damage_types.id"),
        nullable=False,
    )
    modifier_type: Mapped[str] = mapped_column(
        SAEnum(DamageModifierType, name="damagemodifiertype"), nullable=False
    )

    monster: Mapped[Monster] = relationship(
        "Monster", back_populates="damage_modifiers"
    )
    damage_type: Mapped[DamageType] = relationship("DamageType")


class MonsterConditionImmunity(Base):
    """Junction: a Monster is immune to a Condition."""

    __tablename__ = "catalog_monster_condition_immunities"
    __table_args__ = (
        UniqueConstraint(
            "monster_id", "condition_id", name="uq_catalog_monster_condition_immunities"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    monster_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_monsters.id", ondelete="CASCADE"),
        nullable=False,
    )
    condition_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_conditions.id", ondelete="CASCADE"),
        nullable=False,
    )

    monster: Mapped[Monster] = relationship(
        "Monster", back_populates="condition_immunities"
    )
    condition: Mapped[Condition] = relationship("Condition")


class MonsterAction(Base):
    """One action from a Monster's stat block (attacks, multiattack, etc.)."""

    __tablename__ = "catalog_monster_actions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    monster_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_monsters.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    attack_bonus: Mapped[int | None] = mapped_column(Integer, nullable=True)
    save_ability_score_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_ability_score_definitions.id"),
        nullable=True,
    )
    save_dc: Mapped[int | None] = mapped_column(Integer, nullable=True)
    usage_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    usage_times: Mapped[int | None] = mapped_column(Integer, nullable=True)

    monster: Mapped[Monster] = relationship("Monster", back_populates="actions")
    damages: Mapped[list[MonsterActionDamage]] = relationship(
        "MonsterActionDamage", back_populates="action", cascade="all, delete-orphan"
    )


class MonsterActionDamage(Base):
    """A damage roll dealt by a MonsterAction."""

    __tablename__ = "catalog_monster_action_damages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    action_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_monster_actions.id", ondelete="CASCADE"),
        nullable=False,
    )
    damage_dice: Mapped[str] = mapped_column(String(20), nullable=False)
    damage_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("catalog_damage_types.id"), nullable=False
    )

    action: Mapped[MonsterAction] = relationship(
        "MonsterAction", back_populates="damages"
    )
    damage_type: Mapped[DamageType] = relationship("DamageType")


class MonsterLegendaryAction(Base):
    """One legendary action from a Monster's stat block."""

    __tablename__ = "catalog_monster_legendary_actions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    monster_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_monsters.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    attack_bonus: Mapped[int | None] = mapped_column(Integer, nullable=True)
    save_ability_score_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_ability_score_definitions.id"),
        nullable=True,
    )
    save_dc: Mapped[int | None] = mapped_column(Integer, nullable=True)
    usage_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    usage_times: Mapped[int | None] = mapped_column(Integer, nullable=True)

    monster: Mapped[Monster] = relationship(
        "Monster", back_populates="legendary_actions"
    )
    damages: Mapped[list[MonsterLegendaryActionDamage]] = relationship(
        "MonsterLegendaryActionDamage",
        back_populates="action",
        cascade="all, delete-orphan",
    )


class MonsterLegendaryActionDamage(Base):
    """A damage roll dealt by a MonsterLegendaryAction."""

    __tablename__ = "catalog_monster_legendary_action_damages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    action_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_monster_legendary_actions.id", ondelete="CASCADE"),
        nullable=False,
    )
    damage_dice: Mapped[str] = mapped_column(String(20), nullable=False)
    damage_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("catalog_damage_types.id"), nullable=False
    )

    action: Mapped[MonsterLegendaryAction] = relationship(
        "MonsterLegendaryAction", back_populates="damages"
    )
    damage_type: Mapped[DamageType] = relationship("DamageType")


class MonsterReaction(Base):
    """One reaction from a Monster's stat block."""

    __tablename__ = "catalog_monster_reactions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    monster_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_monsters.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    attack_bonus: Mapped[int | None] = mapped_column(Integer, nullable=True)
    save_ability_score_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_ability_score_definitions.id"),
        nullable=True,
    )
    save_dc: Mapped[int | None] = mapped_column(Integer, nullable=True)
    usage_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    usage_times: Mapped[int | None] = mapped_column(Integer, nullable=True)

    monster: Mapped[Monster] = relationship("Monster", back_populates="reactions")
    damages: Mapped[list[MonsterReactionDamage]] = relationship(
        "MonsterReactionDamage", back_populates="action", cascade="all, delete-orphan"
    )


class MonsterReactionDamage(Base):
    """A damage roll dealt by a MonsterReaction."""

    __tablename__ = "catalog_monster_reaction_damages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    action_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_monster_reactions.id", ondelete="CASCADE"),
        nullable=False,
    )
    damage_dice: Mapped[str] = mapped_column(String(20), nullable=False)
    damage_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("catalog_damage_types.id"), nullable=False
    )

    action: Mapped[MonsterReaction] = relationship(
        "MonsterReaction", back_populates="damages"
    )
    damage_type: Mapped[DamageType] = relationship("DamageType")


class MonsterSpecialAbility(Base):
    """One special ability (a passive trait) from a Monster's stat block."""

    __tablename__ = "catalog_monster_special_abilities"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    monster_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_monsters.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    attack_bonus: Mapped[int | None] = mapped_column(Integer, nullable=True)
    save_ability_score_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_ability_score_definitions.id"),
        nullable=True,
    )
    save_dc: Mapped[int | None] = mapped_column(Integer, nullable=True)
    usage_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    usage_times: Mapped[int | None] = mapped_column(Integer, nullable=True)

    monster: Mapped[Monster] = relationship(
        "Monster", back_populates="special_abilities"
    )
    damages: Mapped[list[MonsterSpecialAbilityDamage]] = relationship(
        "MonsterSpecialAbilityDamage",
        back_populates="action",
        cascade="all, delete-orphan",
    )


class MonsterSpecialAbilityDamage(Base):
    """A damage roll dealt by a MonsterSpecialAbility."""

    __tablename__ = "catalog_monster_special_ability_damages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    action_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_monster_special_abilities.id", ondelete="CASCADE"),
        nullable=False,
    )
    damage_dice: Mapped[str] = mapped_column(String(20), nullable=False)
    damage_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("catalog_damage_types.id"), nullable=False
    )

    action: Mapped[MonsterSpecialAbility] = relationship(
        "MonsterSpecialAbility", back_populates="damages"
    )
    damage_type: Mapped[DamageType] = relationship("DamageType")


# --- Rules narrativas (SRD 2014 §7.4.9) --------------------------------------


class RuleSection(CatalogEntityMixin, Base):
    """A top-level section of the rules reference (e.g. Combat, Adventuring).

    Translatable text (`name`, `desc`) lives in `RuleSectionI18n`.
    """

    __tablename__ = "catalog_rule_sections"


class RuleSectionI18n(CatalogI18nMixin, Base):
    """Translated text for a RuleSection."""

    __tablename__ = "catalog_rule_sections_i18n"
    __table_args__ = (
        UniqueConstraint("entity_id", "locale", name="uq_catalog_rule_sections_i18n"),
    )

    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_rule_sections.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    desc: Mapped[str] = mapped_column(Text, nullable=False, default="")


class Rule(CatalogEntityMixin, Base):
    """A single rule entry from the rules reference.

    Translatable text (`name`, `desc`) lives in `RuleI18n`.
    """

    __tablename__ = "catalog_rules"

    sections: Mapped[list[RuleRuleSection]] = relationship(
        "RuleRuleSection", back_populates="rule", cascade="all, delete-orphan"
    )


class RuleI18n(CatalogI18nMixin, Base):
    """Translated text for a Rule."""

    __tablename__ = "catalog_rules_i18n"
    __table_args__ = (
        UniqueConstraint("entity_id", "locale", name="uq_catalog_rules_i18n"),
    )

    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_rules.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    desc: Mapped[str] = mapped_column(Text, nullable=False, default="")


class RuleRuleSection(Base):
    """Junction: a Rule belongs to a RuleSection."""

    __tablename__ = "catalog_rule_rule_sections"
    __table_args__ = (
        UniqueConstraint(
            "rule_id", "rule_section_id", name="uq_catalog_rule_rule_sections"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    rule_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_rules.id", ondelete="CASCADE"),
        nullable=False,
    )
    rule_section_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("catalog_rule_sections.id", ondelete="CASCADE"),
        nullable=False,
    )

    rule: Mapped[Rule] = relationship("Rule", back_populates="sections")
    rule_section: Mapped[RuleSection] = relationship("RuleSection")
