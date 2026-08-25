# Anahita — Backend PRD

## Product Requirements Document | Backend

**Versão:** 1.1
**Data:** 2026-04-08
**Autor:** Felipe Braga

---

## 1. Visão Geral

Anahita é uma plataforma multi-mesa para gerenciamento de campanhas de D&D 5e. Permite que múltiplos Dungeon Masters gerenciem campanhas independentes, com jogadores participando de várias mesas simultaneamente.

### 1.1 Princípio Central

> Não atrapalhar o fluxo da sessão. Tudo que o DM usa durante o jogo precisa ser rápido, com poucos cliques e feedback instantâneo.

### 1.2 Prioridade de Experiência

1. **Rapidez durante a sessão** — combat tracker, quick notes
2. **Preparação pré-sessão** — world-building, plot planning
3. **Compartilhamento com jogadores** — handouts, fichas
4. **Registro pós-sessão** — diário, recap, lore

---

## 2. Stack Tecnológico

| Camada        | Tecnologia                              |
|---------------|----------------------------------------|
| Framework     | Python 3.14+ + FastAPI                       |
| ORM           | SQLAlchemy (async)                     |
| Migrations    | Alembic                               |
| Banco         | PostgreSQL (self-hosted, Docker)       |
| Validação     | Pydantic                              |
| Real-time     | WebSockets nativos (FastAPI/Starlette) |
| Auth          | Própria, strategy pattern extensível   |
| File Storage  | Local (filesystem), extensível p/ S3   |
| Ferramentas   | uv (gerenciamento), taskipy, ruff, mypy |
| Infra         | Docker Compose                         |

### 2.1 Decisões Técnicas Fundamentais

- **Sem Redis.** Combate em turnos é inerentemente síncrono. Postgres é a fonte de verdade para estado de combate. Se o servidor cair, o estado está salvo.
- **Sem JSONB.** Todo o modelo é relacional. Garante portabilidade de banco (SQLite para testes), integridade referencial via FKs e queries previsíveis.
- **Tabelas de junção explícitas** para relacionamentos de world-building. Mais tabelas, mas com FKs reais e sem polimorfismo genérico.
- **Rules engine desacoplada.** Módulo Python puro, sem dependência de FastAPI ou SQLAlchemy. Testável com pytest puro.
- **Storage abstrato.** Interface única para armazenamento de arquivos. Implementação local (filesystem) agora, object storage (S3/R2/B2) no futuro. Arquivos nunca são armazenados no banco — o banco guarda apenas o `storage_key` (string de referência).
- **Sem vendor lock-in.** Nenhuma dependência de serviços gerenciados específicos (Supabase, Vercel, etc.). Tudo roda em Docker Compose numa VPS.
- **i18n relacional no catálogo.** Toda entidade de catálogo com texto traduzível (nome, descrição, etc.) tem uma tabela `*_i18n` separada: `entity_id` (FK), `locale` (string/enum extensível — hoje `en` e `pt-BR`), colunas de texto. Unique `(entity_id, locale)`. A tabela base guarda apenas dados estruturais (números, enums, FKs) e o `index` — o slug estável do SRD (ex. `acid-arrow`), usado como chave de rastreabilidade e de idempotência do seed. Mantém a regra "sem JSONB / sem polimorfismo genérico": nenhuma tabela de tradução genérica tipo EAV, uma tabela `_i18n` por entidade.
- **Conteúdo custom é sempre preso a uma campanha.** Toda entidade de catálogo suporta `is_custom: bool` + `campaign_id: FK nullable`, com a constraint `is_custom = false ⟺ campaign_id IS NULL`. Conteúdo do SRD (`is_custom=false`) é global, read-only, compartilhado por todas as campanhas. Conteúdo homebrew (`is_custom=true`) só existe, é visível e é utilizável dentro da campanha em que foi criado — nunca aparece no catálogo global nem em outra campanha. Regra válida para as 24 categorias de catálogo (seção 7.4), não só Race/Class.

---

## 3. Modelo de Usuários e Acesso

Hierarquia: **User → Campaign (ownership) → CampaignMember (role-based)**.

- Um User pode ser DM em algumas campanhas e jogador em outras.
- O papel (role) é **por campanha**, não global.
- O DM da campanha é o admin daquele espaço: controla visibilidade (notas privadas vs. handouts públicos).
- O token JWT carrega `user_id` mas **não** o role — o role é resolvido no middleware via par `(user_id, campaign_id)` consultando a tabela de memberships.

---

## 4. Autenticação

Sistema próprio, extensível via **strategy pattern**.

### 4.1 Arquitetura

- **AuthStrategy (ABC):** define `authenticate`, `get_current_user`, `refresh_token`.
- **Implementação inicial:** email + senha com JWT.
  - Access token curto + refresh token longo em httpOnly cookie.
  - Refresh token armazenado encriptado no banco.
- **Router de auth desacoplado:** não conhece a estratégia concreta, recebe via dependency injection.

### 4.2 Extensibilidade

- **AuthProvider (tabela):** vincula múltiplos providers a um User (`provider_type`: local, discord, google).
- Para adicionar OAuth2 (ex: Discord), basta registrar uma nova strategy sem tocar nos endpoints.

---

## 5. Armazenamento de Arquivos

### 5.1 Princípio

Arquivos binários (imagens, mapas, tokens) **nunca são armazenados no banco de dados**. O banco guarda apenas um `storage_key` — uma string de referência como `"handouts/campaign_abc/map_01.png"`. O arquivo binário vive no storage.

### 5.2 Interface StorageService

ABC com três métodos:

- `upload(key: str, data: bytes, content_type: str) → str` — grava o arquivo, retorna o key.
- `get_url(key: str) → str` — resolve o key para URL acessível.
- `delete(key: str) → None` — remove o arquivo.

### 5.3 Implementação Local (atual)

**LocalStorageService** salva arquivos em `/data/uploads/{storage_key}`. O Nginx serve diretamente esse diretório como static files em `/files/*` — o request não passa pelo Python.

Organização dos keys por campanha:

```
/data/uploads/
├── handouts/
│   └── {campaign_id}/
│       ├── map_01.png
│       └── letter_from_king.jpg
└── tokens/
    └── {campaign_id}/
        ├── goblin.png
        └── dragon.png
```

### 5.4 Migração Futura (S3/R2/B2)

Criar **S3StorageService** que implementa a mesma interface. Troca via config (variável de ambiente). O `storage_key` no banco permanece idêntico. Nenhum model, schema ou service muda.

---

## 6. Fases de Entrega

### Fase 0 — Catálogo SRD

Modelagem e seed das 24 categorias de referência do SRD 2014 (ver seção 7.4): vocabulário fixo, equipamento, progressão de classe, backgrounds/feats, monstros. Não é uma fase "visível" para o usuário final, mas é pré-requisito de dados para as fases seguintes — sem ela, Character sheet (Fase 1) e Combat tracker (Fase 2) não têm o que popular.

### Fase 1 — Fundação

Fichas de personagem, modelo de campanha, convite de jogadores, gestão básica de sessões com notas. Entrega uma ferramenta usável para o DM organizar a mesa. Consome do catálogo (Fase 0): `Race`/`Subrace`/`RaceTrait`, `ClassDefinition`/`SubclassDefinition`/`Feature`/`ClassLevel`, `Background`, `Feat`, `Spell`, `Item`/`EquipmentCategory`.

### Fase 2 — Sessão ao Vivo

Combat tracker (iniciativa, HP, condições, turnos) e quick notes durante a sessão. Design mobile-first para uso na mesa. WebSocket para estado em tempo real. Consome do catálogo: `Monster` (stat block completo para NPCs/monstros em `EncounterParticipant`), `Condition`, `DamageType`.

### Fase 3 — World-building

Locais, NPCs, facções, relacionamentos entre entidades, links com sessões. Mapas como upload de imagens com pins clicáveis. Full-text search via `tsvector` do Postgres. Consome do catálogo: `Monster` (NPCs com stat block via `NPC.stat_block_id`), `Language`.

### Fase 4 — Loot, Inventário e Compartilhamento

Inventário do grupo, distribuição de loot pós-combate, sistema de handouts (conteúdo liberado pelo DM para jogadores). Consome do catálogo: `Item`, `MagicItem`.

### Fase 5 — Registro e Lore

Diário privado do mestre, recap cronológico das sessões (reaproveita `Session.summary`, sem tabela nova), timeline de eventos híbrida (sessões geram entradas automáticas + mestre adiciona eventos manuais), e wiki da campanha (páginas de lore livre, linkáveis a NPCs/Locais/Facções, entrando na busca cross-entidade da Fase 3). Detalhamento completo em §7.10. Geração de resumo por IA foi cogitada mas fica fora do escopo desta fase — v1 é inteiramente manual.

O suporte i18n do catálogo (seção 2.1) é transversal a todas as fases: qualquer tela que exiba conteúdo de catálogo lê a tradução do locale ativo, com fallback para `en`.

---

## 7. Modelo de Dados

~85 tabelas, organizadas por domínio. Todas relacionais, sem JSONB. A maior parte do crescimento vem do catálogo de referência (seção 7.4): 24 categorias do SRD, cada uma com tabela base + tabela `_i18n` + tabelas filhas para dados aninhados (ver padrão descrito no início da seção 7.4).

### 7.1 Auth & Users

**User**

| Coluna          | Tipo      | Notas                |
|-----------------|-----------|----------------------|
| id              | UUID (PK) |                      |
| email           | String    | unique               |
| username        | String    | unique               |
| hashed_password | String    |                      |
| created_at      | Timestamp |                      |
| updated_at      | Timestamp |                      |

**AuthProvider**

| Coluna           | Tipo      | Notas                      |
|------------------|-----------|----------------------------|
| id               | UUID (PK) |                            |
| user_id          | FK User   |                            |
| provider_type    | Enum      | local, discord, google     |
| provider_user_id | String    | ID externo do provider     |
| created_at       | Timestamp |                            |

### 7.2 Campaigns & Membership

**Campaign**

| Coluna      | Tipo      | Notas                          |
|-------------|-----------|--------------------------------|
| id          | UUID (PK) |                                |
| name        | String    |                                |
| description | Text      |                                |
| setting     | String    | nullable                       |
| owner_id    | FK User   |                                |
| status      | Enum      | active, paused, archived       |
| created_at  | Timestamp |                                |

**CampaignMember**

| Coluna      | Tipo      | Notas                               |
|-------------|-----------|--------------------------------------|
| id          | UUID (PK) |                                      |
| campaign_id | FK        |                                      |
| user_id     | FK User   |                                      |
| role        | Enum      | dm, player                           |
| joined_at   | Timestamp |                                      |

Constraint: unique `(campaign_id, user_id)`.

**CampaignInvite**

| Coluna      | Tipo      | Notas                    |
|-------------|-----------|--------------------------|
| id          | UUID (PK) |                          |
| campaign_id | FK        |                          |
| invite_code | String    | unique                   |
| role        | Enum      | dm, player               |
| expires_at  | Timestamp |                          |
| used_by     | FK User   | nullable                 |

### 7.3 Characters

**Character**

| Coluna              | Tipo      | Notas              |
|---------------------|-----------|---------------------|
| id                  | UUID (PK) |                     |
| campaign_member_id  | FK        |                     |
| name                | String    |                     |
| race_id             | FK Race   |                     |
| subrace_id          | FK        | nullable            |
| level               | Integer   |                     |
| experience_points   | Integer   |                     |
| alignment           | String    |                     |
| background          | String    |                     |
| hit_point_max       | Integer   |                     |
| hit_point_current   | Integer   |                     |
| temporary_hit_points| Integer   |                     |
| armor_class         | Integer   |                     |
| speed               | Integer   |                     |
| inspiration         | Boolean   |                     |
| proficiency_bonus   | Integer   |                     |
| currency_cp         | Integer   | saldo de moeda, normalizado em copper (1 cp / 10 sp / 50 ep / 100 gp / 1000 pp — mesma convenção do preço de itens do catálogo); denominações são um detalhe de exibição do frontend |
| created_at          | Timestamp |                     |

**CharacterAbilityScore**

| Coluna       | Tipo      | Notas                                      |
|--------------|-----------|---------------------------------------------|
| id           | UUID (PK) |                                             |
| character_id | FK        |                                             |
| ability      | Enum      | str, dex, con, int, wis, cha               |
| base_score   | Integer   |                                             |
| asi_bonus    | Integer   |                                             |
| misc_bonus   | Integer   |                                             |

Uma linha por ability, seis por personagem. Modifiers calculados pela rules engine.

**CharacterSkill**

| Coluna       | Tipo      | Notas                                        |
|--------------|-----------|-----------------------------------------------|
| id           | UUID (PK) |                                               |
| character_id | FK        |                                               |
| skill        | Enum      | acrobatics, animal_handling... (18 skills)    |
| proficient   | Boolean   |                                               |
| expertise    | Boolean   |                                               |

Bônus calculado pela engine (ability modifier + proficiency).

**CharacterClass**

| Coluna              | Tipo      | Notas                                 |
|---------------------|-----------|---------------------------------------|
| id                  | UUID (PK) |                                       |
| character_id        | FK        |                                       |
| class_definition_id | FK        |                                       |
| subclass_id         | FK        | nullable                              |
| level               | Integer   |                                       |

Tabela separada para suportar multiclass.

**CharacterFeature**

| Coluna         | Tipo      | Notas                                    |
|----------------|-----------|-------------------------------------------|
| id             | UUID (PK) |                                           |
| character_id   | FK        |                                           |
| source_type    | Enum      | class, feat                               |
| source_name    | String    |                                           |
| feature_name   | String    |                                           |
| description    | Text      |                                           |
| level_acquired | Integer   |                                           |

Features raciais vêm do catálogo Race/RaceTrait. CharacterFeature armazena apenas features de classe e feats.

**CharacterRaceChoice**

| Coluna        | Tipo      | Notas                                       |
|---------------|-----------|----------------------------------------------|
| id            | UUID (PK) |                                              |
| character_id  | FK        |                                              |
| race_trait_id | FK        |                                              |
| chosen_value  | String    | ex: cantrip escolhido pelo High Elf          |

**CharacterSpell**

| Coluna       | Tipo      | Notas                  |
|--------------|-----------|-------------------------|
| id           | UUID (PK) |                         |
| character_id | FK        |                         |
| spell_id     | FK Spell  |                         |
| prepared     | Boolean   |                         |
| source_class | String    |                         |

`level` (círculo) e `ritual` não são persistidos — resolvidos do catálogo (`Spell.level`/`Spell.ritual`) na leitura.

**CharacterSpellSlot**

| Coluna       | Tipo      | Notas                  |
|--------------|-----------|-------------------------|
| id           | UUID (PK) |                         |
| character_id | FK        |                         |
| spell_level  | Integer   | 1-9                     |
| used         | Integer   |                         |

Máximo por nível não é persistido — derivado de `ClassLevelSpellSlot`, somado pelas classes conjuradoras do personagem no nível de cada uma (simplificação: não implementa a tabela combinada de conjurador multiclasse do PHB — exato para classe única, aproximado para multiclasse com duas classes conjuradoras).

**CharacterEquipment**

| Coluna       | Tipo      | Notas        |
|--------------|-----------|---------------|
| id           | UUID (PK) |               |
| character_id | FK        |               |
| item_id      | FK Item   |               |
| equipped     | Boolean   |               |
| quantity     | Integer   |               |
| attunement   | Boolean   |               |

### 7.4 Catálogos de Referência (D&D 5e SRD)

Pré-populados via seeds a partir do SRD 2014 (fonte de referência: `_data/2014/en` e `_data/2014/pt-BR`, vendorizado fora do controle de versão — usado só como vocabulário/spec, não lido em runtime). 24 categorias, organizadas em 7 grupos abaixo. Duas regras se aplicam a **todas** as tabelas-base deste catálogo (seção 2.1):

1. **Custom = preso à campanha.** `is_custom: Boolean` (default `false`) + `campaign_id: FK nullable`, com `is_custom=false ⟺ campaign_id IS NULL`. SRD é global (`campaign_id=null`); homebrew só existe dentro da campanha que o criou.
2. **i18n via tabela `_i18n`.** Toda tabela-base com texto traduzível tem uma tabela irmã `<tabela>_i18n` (`entity_id` FK, `locale`, colunas de texto), unique `(entity_id, locale)`. A tabela base guarda `index` (slug do SRD, ex. `acid-arrow`) para idempotência do seed — homebrew não tem `index` do SRD (nullable). Tabelas puramente estruturais (sem texto livre, ex. `RaceAbilityBonus`) não têm `_i18n`.

As tabelas abaixo omitem `id UUID (PK)`, `is_custom`, `campaign_id` e `created_by_id` quando idênticas ao padrão acima, para focar no que é específico de cada entidade.

#### 7.4.1 Vocabulário fixo

Tabelas pequenas, baixa cardinalidade, sem relações complexas — `AbilityScoreDefinition`, `SkillDefinition`, `Alignment`, `Condition`, `DamageType`, `MagicSchool`, `Language`, `WeaponProperty`. Todas seguem o mesmo formato: tabela base com `index` + campos estruturais, tabela `_i18n` com `name`/`desc`.

| Tabela                  | Campos estruturais (além de index/is_custom/campaign_id) | i18n (`name` + ...)      |
|--------------------------|------------------------------------------------------------|---------------------------|
| AbilityScoreDefinition   | —                                                            | `full_name`, `desc`       |
| SkillDefinition          | `ability_score_id` FK                                       | `desc`                    |
| Alignment                | —                                                            | `abbreviation`, `desc`    |
| Condition                | —                                                            | `desc`                    |
| DamageType               | —                                                            | `desc`                    |
| MagicSchool              | —                                                            | `desc` (nullable)         |
| Language                 | `language_type` Enum (standard, exotic)                     | `desc`, `script`, `typical_speakers` |
| WeaponProperty           | —                                                            | `desc`                    |

#### 7.4.2 Raças

**Race**

| Coluna          | Tipo      | Notas                        |
|-----------------|-----------|-------------------------------|
| id              | UUID (PK) |                               |
| index           | String    | nullable (slug SRD)          |
| speed           | Integer   |                               |
| size            | Enum      | small, medium                 |
| darkvision_range| Integer   | 0 se não tem                  |
| is_custom       | Boolean   | default false                 |
| campaign_id     | FK        | nullable (null = SRD)         |
| created_by_id   | FK User   | nullable                      |

**RaceI18n** — `race_id` FK, `locale`, `name`, `description`, `age`, `alignment_desc`, `size_description`, `language_desc`.

**RaceTrait**

| Coluna            | Tipo      | Notas                                            |
|-------------------|-----------|---------------------------------------------------|
| id                | UUID (PK) |                                                   |
| race_id           | FK Race   |                                                   |
| mechanical_effect | String    | vocabulário estruturado (resistance:fire, etc.)   |

**RaceTraitI18n** — `race_trait_id` FK, `locale`, `trait_name`, `description`.

**Subrace**

| Coluna      | Tipo      | Notas    |
|-------------|-----------|----------|
| id          | UUID (PK) |          |
| race_id     | FK Race   |          |

**SubraceI18n** — `subrace_id` FK, `locale`, `name`, `description`.

**SubraceTrait**

| Coluna            | Tipo      | Notas    |
|-------------------|-----------|----------|
| id                | UUID (PK) |          |
| subrace_id        | FK        |          |
| mechanical_effect | String    |          |

**SubraceTraitI18n** — `subrace_trait_id` FK, `locale`, `trait_name`, `description`.

**RaceAbilityBonus**

| Coluna     | Tipo      | Notas                                             |
|------------|-----------|-----------------------------------------------------|
| id         | UUID (PK) |                                                   |
| race_id    | FK        | nullable                                          |
| subrace_id | FK        | nullable                                          |
| ability    | Enum      | str, dex, con, int, wis, cha                      |
| bonus      | Integer   |                                                   |

Constraint: exatamente um dos dois FKs preenchido.

#### 7.4.3 Habilidades, perícias e proficiências

**Proficiency**

| Coluna              | Tipo      | Notas                                                        |
|---------------------|-----------|---------------------------------------------------------------|
| id                  | UUID (PK) |                                                               |
| index               | String    | nullable                                                      |
| proficiency_type    | Enum      | skill, saving_throw, weapon, armor, tool, other               |
| skill_id            | FK        | nullable — preenchido se proficiency_type=skill               |
| ability_score_id    | FK        | nullable — preenchido se proficiency_type=saving_throw         |
| equipment_category_id | FK      | nullable — preenchido se proficiency_type=weapon/armor/tool    |

FKs nullable e mutuamente exclusivos por `proficiency_type` (referência explícita, não polimorfismo genérico).

**ProficiencyI18n** — `proficiency_id` FK, `locale`, `name`.

**ProficiencyClass** / **ProficiencyRace** — tabelas de junção `(proficiency_id, class_definition_id)` / `(proficiency_id, race_id)`, indicando quais classes/raças concedem aquela proficiência por padrão.

#### 7.4.4 Classes e progressão

**ClassDefinition**

| Coluna                       | Tipo      | Notas                              |
|------------------------------|-----------|-------------------------------------|
| id                           | UUID (PK) |                                     |
| index                        | String    | nullable                            |
| hit_die                      | Integer   | 6, 8, 10, 12                       |
| primary_ability              | String    |                                     |
| saving_throw_proficiencies   | String    | par de abilities                    |
| is_custom                    | Boolean   | default false                       |
| created_by_id                | FK User   | nullable                           |
| campaign_id                  | FK        | nullable (null = SRD)              |

**ClassDefinitionI18n** — `class_definition_id` FK, `locale`, `name`.

**SubclassDefinition**

| Coluna              | Tipo      | Notas                    |
|---------------------|-----------|--------------------------|
| id                  | UUID (PK) |                          |
| class_definition_id | FK        |                          |
| index               | String    | nullable                 |
| is_custom           | Boolean   |                          |
| created_by_id       | FK User   | nullable                 |
| campaign_id         | FK        | nullable                 |

**SubclassDefinitionI18n** — `subclass_definition_id` FK, `locale`, `name`, `description`, `flavor`.

**Feature** — generaliza `ClassLevelFeature`: cobre features de classe *e* subclasse, incluindo sub-features (ex. Fighting Style dentro de uma feature maior).

| Coluna                 | Tipo      | Notas                                             |
|------------------------|-----------|-----------------------------------------------------|
| id                     | UUID (PK) |                                                   |
| index                  | String    | nullable                                          |
| class_definition_id    | FK        | nullable                                          |
| subclass_definition_id | FK        | nullable — exatamente um dos dois preenchido       |
| level                  | Integer   |                                                   |
| parent_feature_id      | FK self   | nullable — sub-feature                            |
| mechanical_effect      | String    | vocabulário estruturado                           |
| is_custom / campaign_id | —         | padrão do catálogo                                |

**FeatureI18n** — `feature_id` FK, `locale`, `feature_name`, `description`.

**FeaturePrerequisite** — `feature_id` FK, `prerequisite_type` (level, feature, spell), `level` nullable, `required_feature_id` FK nullable, `spell_id` FK nullable.

**ClassLevel** — a tabela de progressão por nível (equivalente a `5e-SRD-Levels`).

| Coluna                  | Tipo      | Notas                                    |
|--------------------------|-----------|---------------------------------------------|
| id                      | UUID (PK) |                                            |
| class_definition_id     | FK        |                                            |
| subclass_definition_id  | FK        | nullable                                   |
| level                   | Integer   | 1-20                                       |
| proficiency_bonus       | Integer   | nullable (repete o cálculo da engine, mas alguns níveis têm exceções documentadas no SRD) |
| ability_score_bonuses   | Integer   | nullable                                   |

Unique `(class_definition_id, subclass_definition_id, level)`.

**ClassLevelFeature** — junção `(class_level_id, feature_id)`.

**ClassLevelSpellSlot** — `class_level_id` FK, `spell_level` Integer (0=cantrips_known), `slot_count` Integer.

**ClassLevelResource** — mecânicas específicas por nível (rage_count, ki_points, sneak_attack_dice, sorcery_points, wild_shape_max_cr, martial_arts_dice, etc.), reaproveitando o padrão de vocabulário estruturado já usado em `mechanical_effect` (seção 8.3):

| Coluna         | Tipo    | Notas                                    |
|----------------|---------|---------------------------------------------|
| id             | UUID (PK) |                                          |
| class_level_id | FK      |                                              |
| resource_key   | String  | ex: `rage_count`, `ki_points`, `sneak_attack_dice` |
| value          | String  | ex: `"3"`, `"2d6"`                          |

#### 7.4.5 Magias

**Spell**

| Coluna        | Tipo      | Notas        |
|---------------|-----------|---------------|
| id            | UUID (PK) |               |
| index         | String    | nullable      |
| level         | Integer   | 0 = cantrip  |
| magic_school_id | FK      |               |
| casting_time  | String    |               |
| range         | String    |               |
| duration      | String    |               |
| components    | String    |               |
| ritual        | Boolean   |               |
| concentration | Boolean   |               |
| is_custom     | Boolean   | default false |
| campaign_id   | FK        | nullable      |
| created_by_id | FK User   | nullable      |

**SpellI18n** — `spell_id` FK, `locale`, `name`, `description`, `higher_levels` (nullable).

**SpellClass** — junção `(spell_id, class_definition_id)` — quais classes podem conjurar a magia.

#### 7.4.6 Equipamento e itens mágicos

**EquipmentCategory** — `id`, `index`, i18n (`name`).

**Item**

| Coluna      | Tipo      | Notas                                            |
|-------------|-----------|-----------------------------------------------------|
| id          | UUID (PK) |                                                   |
| index       | String    | nullable                                          |
| item_type   | Enum      | weapon, armor, gear, tool, consumable              |
| equipment_category_id | FK |                                              |
| rarity      | String    | nullable                                          |
| weight      | Float     |                                                   |
| cost        | Integer   | em copper pieces                                  |
| is_custom   | Boolean   | default false                                     |
| campaign_id | FK        | nullable                                          |
| created_by_id | FK User | nullable                                          |

**ItemI18n** — `item_id` FK, `locale`, `name`, `description`.

**ItemProperty** — junção `(item_id, weapon_property_id)`.

**WeaponDetail**

| Coluna            | Tipo      | Notas        |
|-------------------|-----------|---------------|
| id                | UUID (PK) |               |
| item_id           | FK Item   |               |
| damage_dice       | String    | ex: 1d8       |
| damage_type_id    | FK        |               |
| weapon_range      | String    |               |

**ArmorDetail**

| Coluna                | Tipo      | Notas    |
|-----------------------|-----------|----------|
| id                    | UUID (PK) |          |
| item_id               | FK Item   |          |
| base_ac               | Integer   |          |
| dex_bonus_cap         | Integer   | nullable |
| stealth_disadvantage  | Boolean   |          |
| strength_requirement  | Integer   | nullable |

**MagicItem**

| Coluna                | Tipo      | Notas                                    |
|-----------------------|-----------|---------------------------------------------|
| id                    | UUID (PK) |                                            |
| index                 | String    | nullable                                   |
| equipment_category_id | FK       |                                            |
| rarity                | String    |                                            |
| is_variant            | Boolean   |                                            |
| variant_of_id         | FK self   | nullable                                   |
| is_custom / campaign_id | —       | padrão do catálogo                         |

**MagicItemI18n** — `magic_item_id` FK, `locale`, `name`, `description`.

#### 7.4.7 Backgrounds e feats

**Background**

| Coluna         | Tipo      | Notas    |
|----------------|-----------|----------|
| id             | UUID (PK) |          |
| index          | String    | nullable |
| is_custom / campaign_id | — | padrão do catálogo |

**BackgroundI18n** — `background_id` FK, `locale`, `name`, `personality_traits`, `ideals`, `bonds`, `flaws` (texto livre — no SRD são tabelas de rolagem, tratadas aqui como texto descritivo; normalização em tabela de opções fica para uma fase futura se for necessário rolar/escolher via UI).

**BackgroundProficiency** — junção `(background_id, proficiency_id)`.

**BackgroundEquipment** — `(background_id, item_id, quantity)`.

**BackgroundFeature** — `background_id` FK (1:1) + i18n (`feature_name`, `description`).

**Feat**

| Coluna         | Tipo      | Notas    |
|----------------|-----------|----------|
| id             | UUID (PK) |          |
| index          | String    | nullable |
| is_custom / campaign_id | — | padrão do catálogo |

**FeatI18n** — `feat_id` FK, `locale`, `name`, `description`.

**FeatPrerequisite** — `feat_id` FK, `ability_score_id` FK nullable, `minimum_score` Integer.

#### 7.4.8 Monstros (stat blocks)

Substitui o `stat_block_id` solto na tabela `NPC` (seção 7.7): a partir de agora aponta para `Monster`. Mesmo padrão `is_custom`/`campaign_id` do restante do catálogo — um DM pode criar um monstro homebrew, preso à sua campanha.

**Monster**

| Coluna              | Tipo      | Notas                                    |
|---------------------|-----------|---------------------------------------------|
| id                  | UUID (PK) |                                            |
| index               | String    | nullable                                   |
| size                | Enum      | tiny, small, medium, large, huge, gargantuan |
| creature_type       | String    | ex: dragon, humanoid                       |
| creature_subtype    | String    | nullable                                   |
| alignment           | String    |                                            |
| hit_points          | Integer   |                                            |
| hit_dice            | String    | ex: 13d10+52                               |
| challenge_rating    | Float     |                                            |
| xp                  | Integer   |                                            |
| proficiency_bonus   | Integer   | nullable                                   |
| languages           | String    | prose (ex: "Common, Draconic")             |
| strength, dexterity, constitution, intelligence, wisdom, charisma | Integer | seis colunas |
| is_custom / campaign_id | —     | padrão do catálogo                         |

**MonsterI18n** — `monster_id` FK, `locale`, `name`, `description`.

**MonsterSpeed** — `monster_id` FK (1:1), `walk`, `burrow`, `climb`, `fly`, `swim` (String nullable), `hover` (Boolean).

**MonsterSense** — `monster_id` FK (1:1), `passive_perception` Integer, `blindsight`, `darkvision`, `tremorsense`, `truesight` (String nullable).

**MonsterArmorClass** — `monster_id` FK, `ac_type` String, `value` Integer, `condition_id` FK nullable, `description` String nullable (um monstro pode ter múltiplas entradas de AC).

**MonsterProficiency** — `monster_id` FK, `proficiency_id` FK, `value` Integer.

**MonsterDamageModifier** — `monster_id` FK, `damage_type_id` FK, `modifier_type` Enum (vulnerable, resistant, immune).

**MonsterConditionImmunity** — junção `(monster_id, condition_id)`.

**MonsterAction** / **MonsterLegendaryAction** / **MonsterReaction** / **MonsterSpecialAbility** — mesma forma, quatro tabelas (uma por seção do stat block):

| Coluna         | Tipo      | Notas                                  |
|----------------|-----------|--------------------------------------------|
| id             | UUID (PK) |                                            |
| monster_id     | FK        |                                            |
| name           | String    |                                            |
| description    | Text      |                                            |
| attack_bonus   | Integer   | nullable                                   |
| save_ability_score_id | FK | nullable                                   |
| save_dc        | Integer   | nullable                                   |
| usage_type     | String    | nullable (ex: recharge_5_6, per_day)       |
| usage_times    | Integer   | nullable                                   |

**MonsterActionDamage** — `monster_action_id` FK (aponta para qualquer uma das quatro tabelas acima via `source_table` + `source_id` **não** — em vez de polimorfismo genérico, cada uma das quatro tabelas de ação tem sua própria tabela `*Damage` filha: `MonsterActionDamage`, `MonsterLegendaryActionDamage`, `MonsterReactionDamage`, `MonsterSpecialAbilityDamage`, todas com o mesmo shape `(action_id FK, damage_dice String, damage_type_id FK)`.

#### 7.4.9 Regras narrativas

**RuleSection** — `id`, `index`, i18n (`name`, `desc`).

**Rule** — `id`, `index`, i18n (`name`, `desc`); **RuleRuleSection** — junção `(rule_id, rule_section_id)`.

| Coluna          | Tipo      | Notas                        |
|-----------------|-----------|-------------------------------|
| id              | UUID (PK) |                               |
| name            | String    |                               |
| speed           | Integer   |                               |
| size            | Enum      | small, medium                 |
| darkvision_range| Integer   | 0 se não tem                  |
| description     | Text      |                               |
| is_custom       | Boolean   | default false                 |
| campaign_id     | FK        | nullable (null = SRD)         |
| created_by_id   | FK User   | nullable                      |

**RaceTrait**

| Coluna            | Tipo      | Notas                                            |
|-------------------|-----------|---------------------------------------------------|
| id                | UUID (PK) |                                                   |
| race_id           | FK Race   |                                                   |
| trait_name        | String    |                                                   |
| description       | Text      |                                                   |
| mechanical_effect | String    | vocabulário estruturado (resistance:fire, etc.)   |

**Subrace**

| Coluna      | Tipo      | Notas    |
|-------------|-----------|----------|
| id          | UUID (PK) |          |
| race_id     | FK Race   |          |
| name        | String    |          |
| description | Text      |          |

**SubraceTrait**

| Coluna            | Tipo      | Notas    |
|-------------------|-----------|----------|
| id                | UUID (PK) |          |
| subrace_id        | FK        |          |
| trait_name        | String    |          |
| description       | Text      |          |
| mechanical_effect | String    |          |

**RaceAbilityBonus**

| Coluna     | Tipo      | Notas                                             |
|------------|-----------|---------------------------------------------------|
| id         | UUID (PK) |                                                   |
| race_id    | FK        | nullable                                          |
| subrace_id | FK        | nullable                                          |
| ability    | Enum      | str, dex, con, int, wis, cha                      |
| bonus      | Integer   |                                                   |

Constraint: exatamente um dos dois FKs preenchido.

**ClassDefinition**

| Coluna                       | Tipo      | Notas                              |
|------------------------------|-----------|-------------------------------------|
| id                           | UUID (PK) |                                     |
| name                         | String    |                                     |
| hit_die                      | Integer   | 6, 8, 10, 12                       |
| primary_ability              | String    |                                     |
| saving_throw_proficiencies   | String    | par de abilities                    |
| is_custom                    | Boolean   | default false                       |
| created_by_id                | FK User   | nullable                           |
| campaign_id                  | FK        | nullable (null = SRD)              |

**ClassLevelFeature**

| Coluna              | Tipo      | Notas                              |
|---------------------|-----------|-------------------------------------|
| id                  | UUID (PK) |                                     |
| class_definition_id | FK        |                                     |
| level               | Integer   |                                     |
| feature_name        | String    |                                     |
| description         | Text      |                                     |
| mechanical_effect   | String    | vocabulário estruturado             |

**SubclassDefinition**

| Coluna              | Tipo      | Notas                    |
|---------------------|-----------|--------------------------|
| id                  | UUID (PK) |                          |
| class_definition_id | FK        |                          |
| name                | String    |                          |
| description         | Text      |                          |
| is_custom           | Boolean   |                          |
| created_by_id       | FK User   | nullable                 |
| campaign_id         | FK        | nullable                 |

**Spell**

| Coluna        | Tipo      | Notas        |
|---------------|-----------|---------------|
| id            | UUID (PK) |               |
| name          | String    |               |
| level         | Integer   | 0 = cantrip  |
| school        | String    |               |
| casting_time  | String    |               |
| range         | String    |               |
| duration      | String    |               |
| components    | String    |               |
| ritual        | Boolean   |               |
| concentration | Boolean   |               |
| description   | Text      |               |
| higher_levels | Text      | nullable      |

**Item**

| Coluna      | Tipo      | Notas                                            |
|-------------|-----------|---------------------------------------------------|
| id          | UUID (PK) |                                                   |
| name        | String    |                                                   |
| item_type   | Enum      | weapon, armor, gear, consumable, magic_item       |
| rarity      | String    | nullable                                          |
| weight      | Float     |                                                   |
| cost        | Integer   | em copper pieces                                  |
| description | Text      |                                                   |
| properties  | String    | nullable                                          |

**WeaponDetail**

| Coluna            | Tipo      | Notas        |
|-------------------|-----------|---------------|
| id                | UUID (PK) |               |
| item_id           | FK Item   |               |
| damage_dice       | String    | ex: 1d8       |
| damage_type       | String    |               |
| weapon_range      | String    |               |
| weapon_properties | String    |               |

**ArmorDetail**

| Coluna                | Tipo      | Notas    |
|-----------------------|-----------|----------|
| id                    | UUID (PK) |          |
| item_id               | FK Item   |          |
| base_ac               | Integer   |          |
| dex_bonus_cap         | Integer   | nullable |
| stealth_disadvantage  | Boolean   |          |
| strength_requirement  | Integer   | nullable |

### 7.5 Sessions

**Session**

| Coluna         | Tipo      | Notas                                   |
|----------------|-----------|------------------------------------------|
| id             | UUID (PK) |                                          |
| campaign_id    | FK        |                                          |
| session_number | Integer   |                                          |
| title          | String    |                                          |
| scheduled_date | Date      | nullable                                 |
| status         | Enum      | planned, in_progress, completed          |
| dm_notes       | Text      | privado                                  |
| summary        | Text      | público para jogadores                   |
| created_at     | Timestamp |                                          |

**SessionNote**

| Coluna     | Tipo      | Notas                                  |
|------------|-----------|----------------------------------------|
| id         | UUID (PK) |                                        |
| session_id | FK        |                                        |
| author_id  | FK User   |                                        |
| content    | Text      |                                        |
| is_private | Boolean   | true = só o DM vê                      |
| created_at | Timestamp |                                        |

### 7.6 Combat

**Encounter**

| Coluna             | Tipo      | Notas                                |
|--------------------|-----------|---------------------------------------|
| id                 | UUID (PK) |                                       |
| session_id         | FK        |                                       |
| name               | String    |                                       |
| status             | Enum      | preparing, active, completed          |
| current_round      | Integer   |                                       |
| current_turn_order | Integer   |                                       |
| created_at         | Timestamp |                                       |

**EncounterParticipant**

| Coluna               | Tipo      | Notas                                         |
|----------------------|-----------|------------------------------------------------|
| id                   | UUID (PK) |                                                |
| encounter_id         | FK        |                                                |
| character_id         | FK        | nullable (PCs)                                 |
| npc_id               | FK NPC    | nullable (monstros/NPCs)                       |
| name                 | String    | fallback para monstros genéricos               |
| initiative           | Integer   |                                                |
| hit_point_max        | Integer   |                                                |
| hit_point_current    | Integer   |                                                |
| temporary_hit_points | Integer   |                                                |
| armor_class          | Integer   |                                                |
| turn_order           | Integer   |                                                |
| is_active            | Boolean   | false = morto/fugitivo                         |

Regra: um participant é PC **ou** NPC, nunca ambos. Validado na camada de aplicação.

**EncounterCondition**

| Coluna           | Tipo      | Notas                                                 |
|------------------|-----------|--------------------------------------------------------|
| id               | UUID (PK) |                                                        |
| participant_id   | FK        |                                                        |
| condition        | Enum      | blinded, charmed, deafened... (15 condições do 5e)     |
| duration_rounds  | Integer   | nullable (null = indefinido)                           |
| applied_at_round | Integer   |                                                        |

**CombatLog**

| Coluna       | Tipo      | Notas                                                                |
|--------------|-----------|-----------------------------------------------------------------------|
| id           | UUID (PK) |                                                                       |
| encounter_id | FK        |                                                                       |
| round        | Integer   |                                                                       |
| turn_order   | Integer   |                                                                       |
| actor_id     | FK        | EncounterParticipant                                                  |
| action_type  | Enum      | attack, spell, move, dash, dodge, disengage, help, hide, ready, other |
| description  | Text      |                                                                       |
| damage_dealt | Integer   | nullable                                                              |
| damage_type  | String    | nullable                                                              |
| target_id    | FK        | nullable                                                              |
| created_at   | Timestamp |                                                                       |

### 7.7 World-building

**NPC**

| Coluna        | Tipo      | Notas                       |
|---------------|-----------|------------------------------|
| id            | UUID (PK) |                              |
| campaign_id   | FK        |                              |
| name          | String    |                              |
| race          | String    |                              |
| occupation    | String    | nullable                     |
| description   | Text      |                              |
| personality   | Text      | nullable                     |
| is_alive      | Boolean   |                              |
| stat_block_id | FK Monster | nullable (NPCs com stats — catálogo, seção 7.4.8; pode ser SRD ou monstro homebrew da campanha) |
| created_at    | Timestamp |                              |

**Location**

| Coluna             | Tipo      | Notas                                                   |
|--------------------|-----------|----------------------------------------------------------|
| id                 | UUID (PK) |                                                          |
| campaign_id        | FK        |                                                          |
| name               | String    |                                                          |
| location_type      | Enum      | city, town, dungeon, wilderness, building, region, plane |
| description        | Text      |                                                          |
| parent_location_id | FK self   | nullable — hierarquia (região → cidade → taverna)        |

**Faction**

| Coluna          | Tipo      | Notas    |
|-----------------|-----------|----------|
| id              | UUID (PK) |          |
| campaign_id     | FK        |          |
| name            | String    |          |
| description     | Text      |          |
| alignment       | String    | nullable |
| influence_level | String    | nullable |

**Tabelas de Junção (World-building)**

| Tabela                | FKs                          | Campos extras                                                            |
|-----------------------|------------------------------|--------------------------------------------------------------------------|
| NPCFaction            | npc_id, faction_id           | role_in_faction                                                          |
| NPCLocation           | npc_id, location_id          | presence_type (enum: resides, frequents, controls)                       |
| NPCSession            | npc_id, session_id           | appearance_note                                                          |
| LocationSession       | location_id, session_id      | visit_note                                                               |
| FactionRelationship   | faction_a_id, faction_b_id   | relationship_type (enum: allied, hostile, neutral, vassal, trade_partner) |

### 7.8 Handouts

**Handout**

| Coluna       | Tipo      | Notas                                     |
|--------------|-----------|-------------------------------------------|
| id           | UUID (PK) |                                           |
| campaign_id  | FK        |                                           |
| session_id   | FK        | nullable (pode ser geral da campanha)     |
| title        | String    |                                           |
| content      | Text      | nullable (texto do handout)               |
| handout_type | Enum      | text, image, map                          |
| storage_key  | String    | nullable (referência ao arquivo no storage)|
| is_revealed  | Boolean   | default false                             |
| revealed_at  | Timestamp | nullable                                  |
| created_at   | Timestamp |                                           |

O `storage_key` é uma referência abstrata (ex: `handouts/campaign_abc/map.png`). O StorageService resolve para URL ou path. Arquivos binários **nunca** são armazenados no banco.

### 7.9 Inventory

**PartyInventory**

| Coluna      | Tipo      | Notas    |
|-------------|-----------|----------|
| id          | UUID (PK) |          |
| campaign_id | FK        |          |
| item_id     | FK Item   |          |
| quantity    | Integer   |          |
| notes       | String    | nullable |

**LootDrop**

| Coluna           | Tipo      | Notas                          |
|------------------|-----------|--------------------------------|
| id               | UUID (PK) |                                |
| encounter_id     | FK        |                                |
| item_id          | FK        | nullable (itens custom)        |
| custom_item_name | String    | nullable                       |
| quantity         | Integer   |                                |
| currency_cp      | Integer   | tudo convertido pra copper     |
| claimed_by       | FK        | nullable (Character)           |

### 7.10 Registro e Lore

Quatro recursos, com escopos deliberadamente diferentes — nem tudo aqui é uma tabela nova:

- **Diário (`JournalEntry`)**: log privado e cronológico do mestre. Não é visível a jogadores em nenhuma hipótese (não reaproveita o padrão `is_private` de `SessionNote` porque não há caso em que fique público — é sempre DM-only, então a checagem de permissão é simplesmente "requester é o DM da campanha").
- **Recap**: **não introduz tabela nova.** `Session.summary` (PRD §7.5) já existe e já é visível a jogadores — o recap é uma tela de frontend que agrega os `summary` de todas as sessões da campanha em ordem cronológica ("a história até agora"). Nenhuma mudança de backend é necessária além do que `GET /campaigns/{id}/sessions` já retorna.
- **Timeline (`TimelineEvent`)**: híbrida. Cada sessão com `summary` preenchido vira uma entrada *virtual* automática (computada na leitura, nunca persistida — evita duplicar dado e problema de sincronização); o mestre também pode criar eventos manuais (`TimelineEvent`), com data in-game livre e uma posição de ordenação explícita. A leitura funde os dois conjuntos em uma única lista cronológica.
- **Wiki (`WikiPage` + `WikiPageLink`)**: páginas de lore livre em markdown, autoria do mestre, visíveis a todos os membros. Uma página pode linkar a um NPC, Local, ou Facção existente (nunca mais de um por link, mesmo padrão de mutual-exclusion de `LootDrop.item_id`/`magic_item_id`/`custom_item_name`, PRD §7.9) — isso alimenta backlinks ("essa página menciona este NPC") e entra na busca cross-entidade já existente (PRD §10, `app/queries/world_queries.py`), que ganha `wiki_page` como um quarto `entity_type`.

**IA para gerar resumos automaticamente (mencionada na visão da Fase 5, seção 6) fica fora do escopo desta leva** — v1 é 100% manual. Fica registrado como evolução futura possível (ex: um botão "gerar rascunho" no editor de Diário/Recap que chama um LLM sobre as notas de sessão existentes), sem compromisso de quando/se será construído.

**JournalEntry**

| Coluna      | Tipo      | Notas                                          |
|-------------|-----------|-------------------------------------------------|
| id          | UUID (PK) |                                                  |
| campaign_id | FK        |                                                  |
| author_id   | FK User   | sempre o DM da campanha (validado no service)   |
| title       | String    |                                                  |
| content     | Text      |                                                  |
| session_id  | FK        | nullable — vínculo opcional a uma sessão        |
| created_at  | Timestamp |                                                  |

**TimelineEvent** (só os eventos manuais são persistidos — os automáticos são computados a partir de `Session` na leitura, ver acima)

| Coluna       | Tipo      | Notas                                                        |
|--------------|-----------|---------------------------------------------------------------|
| id           | UUID (PK) |                                                                |
| campaign_id  | FK        |                                                                |
| title        | String    |                                                                |
| description  | Text      | nullable                                                      |
| session_id   | FK        | nullable — ancora o evento perto de uma sessão na ordenação   |
| in_game_date | String    | nullable — data livre do calendário da campanha, só exibição  |
| sort_order   | Integer   | posição explícita; eventos automáticos usam `session_number * 1000`, deixando espaço para eventos manuais entre sessões |
| created_at   | Timestamp |                                                                |

**WikiPage**

| Coluna         | Tipo      | Notas                                          |
|----------------|-----------|--------------------------------------------------|
| id             | UUID (PK) |                                                  |
| campaign_id    | FK        |                                                  |
| title          | String    |                                                  |
| slug           | String    | único por campanha, gerado do título, usado na URL |
| content        | Text      | markdown                                        |
| tags           | String    | nullable, lista livre separada por vírgula      |
| created_by_id  | FK User   | nullable                                        |
| created_at     | Timestamp |                                                  |

**WikiPageLink**

| Coluna       | Tipo      | Notas                                                    |
|--------------|-----------|------------------------------------------------------------|
| id           | UUID (PK) |                                                              |
| wiki_page_id | FK        |                                                              |
| npc_id       | FK        | nullable — mutuamente exclusivo com `location_id`/`faction_id` |
| location_id  | FK        | nullable                                                     |
| faction_id   | FK        | nullable                                                     |

### 7.10.1 Endpoints

| Método/Rota                                    | Permissão      | Notas                                             |
|-------------------------------------------------|----------------|----------------------------------------------------|
| `POST /campaigns/{id}/journal`                  | DM only        |                                                      |
| `GET /campaigns/{id}/journal`                   | DM only        | mais recente primeiro                               |
| `PATCH /journal/{entryId}`                      | DM only        |                                                      |
| `DELETE /journal/{entryId}`                     | DM only        |                                                      |
| `GET /campaigns/{id}/timeline`                  | qualquer membro| funde eventos automáticos (sessões) e manuais       |
| `POST /campaigns/{id}/timeline`                 | DM only        | evento manual                                       |
| `PATCH /timeline/{eventId}`                     | DM only        | só eventos manuais                                  |
| `DELETE /timeline/{eventId}`                    | DM only        | só eventos manuais                                  |
| `GET /campaigns/{id}/wiki`                      | qualquer membro| lista resumida (id/title/tags)                      |
| `GET /wiki/{pageId}`                            | qualquer membro| página completa + links                             |
| `POST /campaigns/{id}/wiki`                     | DM only        |                                                      |
| `PATCH /wiki/{pageId}`                          | DM only        |                                                      |
| `DELETE /wiki/{pageId}`                         | DM only        |                                                      |
| `POST /wiki/{pageId}/links`                     | DM only        | vincula a um NPC/Local/Facção                       |
| `DELETE /wiki/{pageId}/links/{linkId}`          | DM only        |                                                      |

O recap não tem endpoint próprio — consome `GET /campaigns/{id}/sessions` (PRD §7.5), já existente.

---

## 8. Rules Engine

Módulo Python puro. Sem imports de FastAPI, SQLAlchemy ou qualquer dependência de I/O. Recebe dataclasses, devolve resultados calculados.

### 8.1 Responsabilidades

| Área               | Descrição                                                                                        |
|--------------------|--------------------------------------------------------------------------------------------------|
| Ability Modifiers  | `(score - 10) // 2`                                                                              |
| Proficiency Bonus  | Baseado no level total do personagem                                                             |
| Skill Bonus        | ability modifier + proficiency (se proficiente) + expertise (se aplicável)                       |
| Armor Class        | Regras por tipo: light (DEX total), medium (DEX até +2), heavy (ignora DEX)                     |
| Hit Points         | Baseado em classe (hit die), level, CON modifier e bônus                                         |
| Attack/Save DC     | Attack roll bonus, spell save DC (8 + proficiency + ability mod)                                 |
| Condições          | Mapeia condições ativas para efeitos mecânicos (blinded → disadvantage em attacks, etc.)         |
| Validações         | Level up, requisitos de multiclass, spells preparadas, attunement slots                          |

### 8.2 Interface

Design funcional — funções puras:

```
calculate_modifier(score: int) → int
calculate_proficiency_bonus(total_level: int) → int
calculate_skill_bonus(ability_mod, proficient, expertise, prof_bonus) → int
calculate_ac(armor: ArmorData, dex_mod, shield, bonuses) → int
calculate_attack_bonus(ability_mod, prof_bonus, bonuses) → int
calculate_save_dc(ability_mod, prof_bonus) → int
get_condition_effects(conditions: list[Condition]) → list[MechanicalEffect]
validate_multiclass(current_classes, new_class, ability_scores) → ValidationResult
```

Tipos de entrada/saída definidos em `engine/types.py` como dataclasses puras.

### 8.3 Class Handlers

Registry de handlers por classe para regras específicas (Sneak Attack, Rage, Wild Shape, etc.).

**Interface ClassHandler:**

```
modify_ac(base_ac: int, context: CharacterContext) → int
modify_attack(base_bonus: int, context: AttackContext) → int
on_level_up(context: LevelUpContext) → LevelUpResult
get_class_resources(level: int) → list[ClassResource]
```

**Handlers do SRD:** classes Python registradas no startup.

**Classes customizadas:** `GenericClassHandler` lê `ClassDefinition` e `ClassLevelFeature` do banco e interpreta `mechanical_effect` via vocabulário declarativo.

**Vocabulário de efeitos mecânicos:**

```
extra_attack, spellcasting, resistance:{type}, bonus_ac:{formula},
proficiency:{skill_or_tool}, darkvision:{range}, speed_bonus:{value},
damage_bonus:{dice}, saving_throw_advantage:{condition}
```

**Resolução no registry:** consulta por `class_definition_id`. Se não encontra handler especializado, usa `GenericClassHandler`. Classes do SRD têm comportamento otimizado em código; classes custom funcionam via dados, sem deploy.

---

## 9. Estrutura do Projeto

```
anahita/
├── backend/
│   ├── alembic/
│   │   ├── versions/
│   │   └── env.py
│   ├── app/
│   │   ├── core/
│   │   │   ├── config.py            # Settings via pydantic-settings
│   │   │   ├── database.py          # async engine, sessionmaker
│   │   │   ├── dependencies.py      # get_db, get_current_user
│   │   │   ├── security.py          # hashing, JWT encode/decode
│   │   │   └── storage/
│   │   │       ├── base.py          # StorageService ABC
│   │   │       ├── local.py         # LocalStorageService
│   │   │       └── s3.py            # futuro
│   │   ├── auth/
│   │   │   ├── models.py
│   │   │   ├── domain.py
│   │   │   ├── schemas.py
│   │   │   ├── strategies/
│   │   │   │   ├── base.py          # AuthStrategy ABC
│   │   │   │   ├── local.py         # email + senha
│   │   │   │   └── discord.py       # futuro
│   │   │   ├── service.py
│   │   │   └── router.py
│   │   ├── campaigns/
│   │   │   ├── models.py
│   │   │   ├── domain.py
│   │   │   ├── schemas.py
│   │   │   ├── service.py
│   │   │   └── router.py
│   │   ├── characters/
│   │   │   ├── models.py
│   │   │   ├── domain.py
│   │   │   ├── schemas.py
│   │   │   ├── service.py
│   │   │   └── router.py
│   │   ├── sessions/
│   │   │   ├── models.py
│   │   │   ├── domain.py
│   │   │   ├── schemas.py
│   │   │   ├── service.py
│   │   │   └── router.py
│   │   ├── combat/
│   │   │   ├── models.py
│   │   │   ├── domain.py            # CombatState, lógica de turnos
│   │   │   ├── schemas.py
│   │   │   ├── service.py
│   │   │   ├── ws_manager.py        # WebSocket connection manager
│   │   │   ├── ws_router.py         # WebSocket endpoints
│   │   │   └── router.py            # REST endpoints
│   │   ├── world/
│   │   │   ├── models.py
│   │   │   ├── domain.py
│   │   │   ├── schemas.py
│   │   │   ├── service.py
│   │   │   └── router.py
│   │   ├── handouts/
│   │   │   ├── models.py
│   │   │   ├── domain.py
│   │   │   ├── schemas.py
│   │   │   ├── service.py
│   │   │   └── router.py
│   │   ├── inventory/
│   │   │   ├── models.py
│   │   │   ├── domain.py
│   │   │   ├── schemas.py
│   │   │   ├── service.py
│   │   │   └── router.py
│   │   ├── catalog/
│   │   │   ├── models.py
│   │   │   ├── schemas.py
│   │   │   ├── service.py
│   │   │   └── router.py
│   │   ├── queries/                  # Queries cross-domain e complexas
│   │   │   ├── world_queries.py
│   │   │   ├── combat_queries.py
│   │   │   └── ...
│   │   └── main.py
│   ├── engine/                        # Python puro, sem dependência de framework
│   │   ├── abilities.py
│   │   ├── armor_class.py
│   │   ├── combat.py
│   │   ├── conditions.py
│   │   ├── hit_points.py
│   │   ├── validation.py
│   │   ├── class_handlers/
│   │   │   ├── base.py               # ClassHandler ABC
│   │   │   ├── generic.py            # GenericClassHandler
│   │   │   ├── fighter.py
│   │   │   ├── wizard.py
│   │   │   └── ...
│   │   ├── types.py                  # dataclasses da engine
│   │   └── registry.py
│   ├── tests/
│   │   ├── engine/                   # testes puros, sem banco
│   │   ├── integration/              # testes com banco
│   │   └── conftest.py
│   ├── seeds/
│   │   ├── spells.py
│   │   ├── items.py
│   │   ├── races.py
│   │   └── classes.py
│   ├── alembic.ini
│   ├── pyproject.toml
│   └── Dockerfile
├── frontend/
│   └── ...                           # Detalhado no PRD Frontend
├── compose.yaml
└── README.md
```

### 9.1 Convenções por Domínio

| Arquivo      | Responsabilidade                                      |
|-------------|-------------------------------------------------------|
| models.py   | SQLAlchemy models (persistência)                      |
| domain.py   | Objetos de domínio, lógica de negócio                 |
| schemas.py  | Pydantic DTOs (request/response da API)               |
| service.py  | Orquestração + queries simples (3-4 linhas)           |
| router.py   | Endpoints HTTP                                        |

Queries complexas ou cross-domain vão para `app/queries/`.

---

## 10. WebSocket — Combat Tracker e Handouts

### 10.1 Conexão

- Endpoint combat: `/ws/combat/{encounter_id}`
- Auth: token JWT como query param
- Validação: verifica membership na campanha
- `WSConnectionManager`: dict de `encounter_id → list[WebSocket]`

### 10.2 Protocolo de Mensagens — Combat

Envelope: `{ "event_type": "...", "payload": {...} }`

**Servidor → Clientes:**

| Evento                    | Descrição                                    |
|---------------------------|----------------------------------------------|
| state_sync                | Estado completo (conexão + após mudanças)    |
| turn_advanced             | Indica de quem é o turno atual               |
| participant_updated       | HP mudou, condição adicionada/removida       |
| encounter_status_changed  | Combate iniciou/encerrou                     |

**Cliente (DM apenas) → Servidor:**

| Evento              | Descrição                       |
|---------------------|---------------------------------|
| advance_turn        | Próximo turno                   |
| update_participant  | Dano, cura, condição            |
| add_participant     | Monstro entra no combate        |
| remove_participant  | Retira participante             |
| end_encounter       | Encerra o combate               |

### 10.3 Handout Reveal via WebSocket

Durante a sessão (WebSocket de combat ativo), o DM pode revelar handouts. O evento `handout_revealed` é enviado via broadcast para jogadores conectados, com o payload contendo id, título, tipo e URL do conteúdo.

Fora da sessão, jogadores veem handouts revelados normalmente via REST (filtro `is_revealed=true`).

### 10.4 Permissões

Apenas `role=dm` pode enviar comandos. Jogadores são read-only. Validação no servidor a cada mensagem.

### 10.5 Tolerância a Falhas

- Desconexão: reconecta e recebe `state_sync` completo.
- Fonte de verdade: Postgres, não WebSocket.
- Fallback: qualquer estado reconstituível via REST.

---

## 11. Deploy — Docker Compose

### 11.1 Topologia

```
┌─────────┐     ┌─────────┐     ┌──────────┐     ┌──────────┐
│  Nginx  │────▶│ Frontend│     │ Backend  │     │ Postgres │
│ :80/443 │────▶│ :3000   │     │ :8000    │     │ :5432    │
└─────────┘     └─────────┘     └──────────┘     └──────────┘
     │                                │                │
     │          /api/* ──────────────▶│                │
     │          /files/* ─▶ static    │───────────────▶│
     │          /* ──────▶ frontend   │
     │
     └── /data/uploads (read-only, serve static files)
```

### 11.2 Serviços

| Serviço   | Imagem                        | Notas                                        |
|-----------|-------------------------------|----------------------------------------------|
| nginx     | nginx:alpine                  | Reverse proxy, SSL (Let's Encrypt), static   |
| frontend  | Node.js (standalone output)   | `next build` + `next start`                  |
| backend   | Python (uvicorn)              | FastAPI                                       |
| postgres  | postgres:18-alpine            | Volume persistido                             |

### 11.3 Volumes

| Volume        | Montagem                               | Notas                              |
|---------------|----------------------------------------|------------------------------------|
| postgres_data | postgres:/var/lib/postgresql/data      | Dados do banco                     |
| upload_data   | backend:/data/uploads (rw)             | Escrita de arquivos                |
|               | nginx:/data/uploads (ro)               | Serve static files                 |

---

## 12. Glossário

| Termo            | Definição                                                                 |
|------------------|---------------------------------------------------------------------------|
| Campaign         | Uma campanha de D&D 5e com seu próprio mundo, jogadores e sessões        |
| DM               | Dungeon Master — administrador de uma campanha                           |
| Encounter        | Um combate dentro de uma sessão                                          |
| Handout          | Conteúdo (texto/imagem/mapa) revelado pelo DM para jogadores             |
| Membership       | Vínculo de um User com uma Campaign, incluindo role                      |
| Rules Engine     | Módulo Python puro que implementa as mecânicas do D&D 5e                 |
| SRD              | System Reference Document — conteúdo do D&D 5e de uso livre             |
| Seed             | Dados pré-populados do SRD (spells, items, races, classes)               |
| Class Handler    | Componente da engine que implementa regras específicas de uma classe     |
| Generic Handler  | Handler que interpreta classes customizadas via dados do banco           |
| Storage Key      | Referência abstrata a um arquivo no storage (nunca path absoluto)        |
| StorageService   | Interface abstrata para upload/download de arquivos                      |
| Stat Block       | Ficha de atributos/ações de um monstro ou NPC (tabela `Monster`, seção 7.4.8) |
| Locale           | Idioma de uma tradução de catálogo (`en`, `pt-BR`, extensível)           |
| i18n             | Padrão relacional de tradução: tabela `_i18n` irmã de cada tabela de catálogo com texto |
| Feature          | Habilidade concedida por classe/subclasse em um nível (tabela `Feature`, seção 7.4.4) — distinto de Trait, que é racial |
| Trait            | Habilidade racial (tabela `RaceTrait`/`SubraceTrait`, seção 7.4.2) — distinto de Feature, que é de classe |
