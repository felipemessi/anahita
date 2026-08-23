"""Shared declarative mixins for the catalog domain.

## Padrão i18n relacional

Toda entidade de catálogo com texto traduzível segue a mesma convenção, em vez
de JSONB ou de uma tabela genérica de traduções:

- A tabela-base (`CatalogEntityMixin`) guarda só dados estruturais e um
  `index` opcional — o slug do SRD (ex. `acid-arrow`), usado para idempotência
  do seed. Conteúdo homebrew não tem `index` do SRD, por isso é nullable.
- Uma tabela irmã `<tabela>_i18n` (`CatalogI18nMixin`) guarda as colunas de
  texto (`name`, `desc`, etc.), com uma FK `entity_id` para a tabela-base, um
  `locale` (`String(5)`, hoje `en`/`pt-BR`) e `UNIQUE(entity_id, locale)`.
- A leitura traduzida nunca falha por falta de tradução: quando o locale ativo
  não tem linha `_i18n`, cai para `en`. Ver `get_translated` em
  `app/catalog/service.py` — helper único, reaproveitado por todos os
  catálogos.

## Conteúdo custom preso à campanha

Toda entidade de catálogo (`CatalogEntityMixin`) também segue a regra de
conteúdo custom (seção 7.4 do PRD): `is_custom: bool` (default `False`) +
`campaign_id: FK nullable`, com a invariante
`is_custom is False ⟺ campaign_id is None`. SRD é global (`campaign_id=None`);
homebrew só existe, é visível e é utilizável dentro da campanha em que foi
criado.

A invariante é validada uma única vez em `app.catalog.domain.
validate_custom_campaign_scope`, reaproveitada por todo `service.py` que criar
conteúdo custom, e reforçada por uma `CHECK` constraint (`__table_args__`
abaixo) aplicada automaticamente a toda tabela que usa `CatalogEntityMixin`.
"""

import uuid
from typing import Any, ClassVar

from sqlalchemy import Boolean, CheckConstraint, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, declared_attr, mapped_column


class CatalogEntityMixin:
    """Columns shared by every catalog base table (SRD global or campaign homebrew)."""

    # Declared by every subclass as a plain `__tablename__ = "..."` attribute
    # (SQLAlchemy declarative convention) — annotated here so `__table_args__`
    # below can reference it.
    __tablename__: str

    #: Subclasses with extra table-level constraints (e.g. Proficiency's
    #: mutually-exclusive reference CHECK) override this instead of redeclaring
    #: `__table_args__`, so the custom/campaign-scope CHECK below is never lost.
    _extra_table_args: ClassVar[tuple[Any, ...]] = ()

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    index: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    is_custom: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # FK to campaigns.id — enforced at DB level in migration, omitted here to
    # avoid cross-domain metadata coupling (campaigns domain not yet implemented).
    campaign_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    # FK to users.id — enforced at DB level in migration.
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    @declared_attr.directive
    @classmethod
    def __table_args__(cls) -> tuple[Any, ...]:
        """Reinforce ``is_custom is False <=> campaign_id is None`` at the DB level."""
        return (
            CheckConstraint(
                "(NOT is_custom AND campaign_id IS NULL) "
                "OR (is_custom AND campaign_id IS NOT NULL)",
                name=f"ck_{cls.__tablename__}_custom_campaign_scope",
            ),
            *cls._extra_table_args,
        )


class CatalogI18nMixin:
    """Columns shared by every `_i18n` sibling table."""

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    locale: Mapped[str] = mapped_column(String(5), nullable=False)
