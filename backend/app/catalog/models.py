"""SQLAlchemy models for the catalog domain (D&D 5e SRD reference data)."""

import uuid

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.catalog.domain import CreatureSize
from app.database import Base


class Race(Base):
    """A playable race from the SRD or a campaign homebrew."""

    __tablename__ = "catalog_races"

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
